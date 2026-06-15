import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx
from typing import Optional

from ...database import get_db
from ...models import StoreDoc, StoreDocTable, StoreDocTableSgtin, GisMtMetadata
from ...schemas import DocumentCreate, DocumentResponse, DocumentListItem
from ...engine.number_generator import generate_number
from ...engine.store_engine import store_calc_doc
from ...config import CONNECTOR_URL

router = APIRouter()
logger = logging.getLogger("his-adapter")


def _notify_connector(doc_id: int, db: Session) -> dict:
    """Собрать данные и отправить запрос на запуск саги выбытия в GIS-MT Connector."""
    meta = db.query(GisMtMetadata).filter(GisMtMetadata.doc_id == doc_id).first()
    if not meta:
        return {"saga_id": None, "status": "NO_METADATA"}

    doc = db.query(StoreDoc).filter(StoreDoc.id == doc_id).first()
    sgtins = []
    for row in doc.rows:
        for s in row.sgtins:
            sgtins.append(s.sgtin)

    if not sgtins:
        return {"saga_id": None, "status": "NO_SGTINS"}

    payload = {
        "sntins": sgtins,
        "dropout_reason": meta.dropout_reason,
        "source_doc_type": meta.source_doc_type,
        "source_doc_date": meta.source_doc_date.isoformat(),
        "source_doc_num": meta.source_doc_num,
        "source_doc_name": meta.source_doc_name or "Акт списания",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{CONNECTOR_URL}/api/v1/sagas/write-off", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                saga_id = data.get("saga_id")
                status = data.get("status", "UNKNOWN")
                return {"saga_id": saga_id, "status": status}
            else:
                logger.error("Connector returned %d: %s", resp.status_code, resp.text)
                return {"saga_id": None, "status": "CONNECTOR_ERROR", "error": resp.text[:500]}
    except Exception as e:
        logger.exception("Failed to call GIS-MT Connector")
        return {"saga_id": None, "status": "CONNECTOR_UNAVAILABLE", "error": str(e)}


@router.post("/documents/draft", response_model=dict)
def create_draft(doc: DocumentCreate, db: Session = Depends(get_db)):
    """Создаёт черновик документа (ISCLOSE = 0) с указанными позициями и SGTIN."""
    new_doc = StoreDoc(
        doctype_id=doc.doctype_id,
        number="",
        date_fact=20260422,
        is_close=0,
        store_from=doc.store_from,
        store_to=doc.store_to,
        org_id=1
    )
    db.add(new_doc)
    db.flush()

    new_doc.number = generate_number(doc.doctype_id, new_doc.id)

    for item in doc.items:
        row = StoreDocTable(
            doc_id=new_doc.id,
            service_id=item.service_id,
            num=item.quantity
        )
        db.add(row)
        db.flush()
        for sgtin_obj in item.sgtins:
            sgtin_clean = sgtin_obj.sgtin.replace('\\u001d', '\x1d')
            sgtin = StoreDocTableSgtin(
                doc_table_id=row.id,
                sgtin=sgtin_clean
            )
            db.add(sgtin)

    if doc.doctype_id == 2 and doc.dropout_reason and doc.source_doc_date:
        gis_meta = GisMtMetadata(
            doc_id=new_doc.id,
            dropout_reason=doc.dropout_reason,
            source_doc_type=doc.source_doc_type or "OTHER",
            source_doc_date=doc.source_doc_date,
            source_doc_num=doc.source_doc_num or new_doc.number,
            source_doc_name=doc.source_doc_name or "Акт списания",
            gis_mt_status="PENDING"
        )
        db.add(gis_meta)

    db.commit()
    return {"doc_id": new_doc.id, "number": new_doc.number}


@router.post("/documents/{doc_id}/approve")
def approve_document(doc_id: int, db: Session = Depends(get_db)):
    """Утверждает документ (ISCLOSE = 1) с проверкой остатков и обновлением статусов SGTIN."""
    doc = db.query(StoreDoc).filter(StoreDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    if doc.is_close == 1:
        raise HTTPException(status_code=400, detail="Документ уже утверждён")

    doc.is_close = 1
    try:
        store_calc_doc(db, doc_id)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))

    saga_result = None
    if doc.doctype_id == 2:
        gis_meta = db.query(GisMtMetadata).filter(GisMtMetadata.doc_id == doc_id).first()
        if gis_meta:
            saga_result = _notify_connector(doc_id, db)
            if saga_result:
                gis_meta.saga_id = saga_result.get("saga_id")
                gis_meta.gis_mt_status = saga_result.get("status", "ERROR")
                if "error" in saga_result:
                    gis_meta.gis_mt_errors = saga_result.get("error")
                db.commit()

    return {
        "status": "approved",
        "doc_id": doc_id,
        "saga": saga_result
    }


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Возвращает полную информацию о документе, включая состав и SGTIN."""
    doc = db.query(StoreDoc).filter(StoreDoc.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    items = []
    for row in doc.rows:
        sgtins = [{"sgtin": s.sgtin} for s in row.sgtins]
        items.append({
            "service_id": row.service_id,
            "quantity": row.num,
            "sgtins": sgtins
        })
    return DocumentResponse(
        id=doc.id,
        doctype_id=doc.doctype_id,
        number=doc.number,
        date_fact=doc.date_fact,
        is_close=doc.is_close,
        store_from=doc.store_from,
        store_to=doc.store_to,
        items=items
    )


# ----- НОВЫЙ ЭНДПОИНТ ДЛЯ МОНИТОРИНГА -----
@router.get("/documents", response_model=list[DocumentListItem])
def list_documents(
    store_id: Optional[int] = Query(None, description="Фильтр по складу"),
    limit: int = Query(50, description="Количество документов"),
    db: Session = Depends(get_db)
):
    """Возвращает список последних документов с информацией о статусе в ГИС МТ."""
    query = db.query(StoreDoc).outerjoin(GisMtMetadata).order_by(StoreDoc.id.desc())
    
    if store_id is not None:
        query = query.filter(
            (StoreDoc.store_from == store_id) | (StoreDoc.store_to == store_id)
        )
    
    docs = query.limit(limit).all()
    
    result = []
    for doc in docs:
        result.append(
            DocumentListItem(
                id=doc.id,
                doctype_id=doc.doctype_id,
                number=doc.number,
                date_fact=doc.date_fact,
                is_close=doc.is_close,
                store_from=doc.store_from,
                store_to=doc.store_to,
                saga_id=doc.gis_meta.saga_id if doc.gis_meta else None,
                gis_mt_status=doc.gis_meta.gis_mt_status if doc.gis_meta else None,
                gis_mt_errors=doc.gis_meta.gis_mt_errors if doc.gis_meta else None,
            )
        )
    return result