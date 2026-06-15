from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient
from ..dependencies import get_http_client, get_his_adapter_url, get_connector_url
from ..services.his_client import HisAdapterClient
from ..services.connector_client import ConnectorClient
from ..schemas import WriteOffRequest, WriteOffResponse, MoveRequest, SagaStatusResponse
import logging

router = APIRouter(tags=["operations"])
logger = logging.getLogger("bff")

@router.post("/operations/write-off", response_model=WriteOffResponse)
async def create_write_off(
    req: WriteOffRequest,
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
):
    his = HisAdapterClient(http_client, his_url)

    # Формируем данные для HIS
    his_items = []
    for item in req.items:
        sgtin_objs = [{"sgtin": s} for s in item.sgtins]
        his_items.append({
            "service_id": item.service_id,
            "quantity": item.quantity,
            "sgtins": sgtin_objs,
        })

    draft_data = {
        "doctype_id": req.doctype_id,
        "store_from": req.store_from,
        "store_to": req.store_to,
        "items": his_items,
        # Метаданные для ГИС МТ — сохраняются в GIS_MT_METADATA при создании черновика
        "dropout_reason": req.dropout_reason,
        "source_doc_type": req.source_doc_type,
        "source_doc_date": req.source_doc_date.isoformat() if req.source_doc_date else None,
        "source_doc_num": req.source_doc_num,
        "source_doc_name": req.source_doc_name,
    }

    try:
        draft_resp = await his.create_draft(draft_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"HIS Adapter error: {str(e)}")

    doc_id = draft_resp["doc_id"]
    doc_number = draft_resp["number"]

    # Сага больше не запускается здесь — она стартует при утверждении в HIS Adapter
    return WriteOffResponse(
        doc_id=doc_id,
        doc_number=doc_number,
        saga_id=None,
        saga_status=None,
        saga_errors=None,
    )


@router.post("/operations/move", response_model=WriteOffResponse)
async def create_move(
    req: MoveRequest,
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
):
    """Создаёт черновик перемещения (doctype_id=3) без взаимодействия с ГИС МТ."""
    his = HisAdapterClient(http_client, his_url)

    his_items = []
    for item in req.items:
        sgtin_objs = [{"sgtin": s} for s in item.sgtins]
        his_items.append({
            "service_id": item.service_id,
            "quantity": item.quantity,
            "sgtins": sgtin_objs,
        })

    draft_data = {
        "doctype_id": 3,  # фиксированный тип — перемещение
        "store_from": req.store_from,
        "store_to": req.store_to,
        "items": his_items,
    }

    try:
        draft_resp = await his.create_draft(draft_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"HIS Adapter error: {str(e)}")

    doc_id = draft_resp["doc_id"]
    doc_number = draft_resp["number"]

    return WriteOffResponse(
        doc_id=doc_id,
        doc_number=doc_number,
        saga_id=None,  # перемещение не порождает сагу
        saga_status=None,
        saga_errors=None,
    )


@router.get("/operations/{saga_id}/status", response_model=SagaStatusResponse)
async def get_operation_status(
    saga_id: str,
    http_client: AsyncClient = Depends(get_http_client),
    connector_url: str = Depends(get_connector_url),
):
    connector = ConnectorClient(http_client, connector_url)
    try:
        status_data = await connector.get_saga_status(saga_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Connector error: {str(e)}")
    return SagaStatusResponse(**status_data)