from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from ...database import get_db
from ...models import Service, SgtinRegistry
from ...schemas import NomenclatureItem

router = APIRouter()

@router.get("/nomenclature", response_model=list[NomenclatureItem])
def get_nomenclature(
    search: str = Query(None, description="Поиск по наименованию"),
    store_id: int = Query(None, description="Фильтр по складу"),
    db: Session = Depends(get_db)
):
    query = db.query(Service).options(joinedload(Service.measure_unit))
    if search:
        query = query.filter(Service.name.ilike(f"%{search}%"))
    if store_id is not None:
        query = query.filter(Service.store_id == store_id)
    services = query.all()

    result = []
    for s in services:
        item = {
            "id": s.id,
            "name": s.name,
            "gtin": s.gtin,
            "is_marked": s.is_marked,
            "rest": s.rest,
            "store_id": s.store_id,
            "measure_unit_code": s.measure_unit.code if s.measure_unit else None,
            "measure_unit_alias": s.measure_unit.alias if s.measure_unit else None,
            "is_allow_sale_in_parts": s.is_allow_sale_in_parts,
        }
        result.append(item)
    return result


@router.get("/nomenclature/{service_id}/sgtins")
def get_sgtins_for_service(service_id: int, db: Session = Depends(get_db)):
    sgtins = db.query(SgtinRegistry).filter(
        SgtinRegistry.service_id == service_id,
        SgtinRegistry.status == 'AVAILABLE'
    ).all()
    return [{"id": s.id, "sgtin": s.sgtin} for s in sgtins]