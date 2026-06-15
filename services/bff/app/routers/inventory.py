from fastapi import APIRouter, Depends, HTTPException, Query
from httpx import AsyncClient
from typing import List, Optional
import asyncio

from ..dependencies import get_http_client, get_his_adapter_url
from ..services.his_client import HisAdapterClient
from ..schemas import InventoryItem

router = APIRouter(tags=["inventory"])

@router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory(
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
    search: Optional[str] = Query(None, description="Поиск по наименованию"),
    store_id: Optional[int] = Query(None, description="Фильтр по складу"),
):
    his = HisAdapterClient(http_client, his_url)
    try:
        nomenclature = await his.get_nomenclature(search=search, store_id=store_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=503, detail=str(e))

    async def enrich_item(item):
        if item.get("is_marked") == 1:
            try:
                sgtins_resp = await his.get_sgtins(item["id"])
                sgtins = [s["sgtin"] for s in sgtins_resp]
            except Exception:
                sgtins = []
        else:
            sgtins = []

        return InventoryItem(
            id=item["id"],
            name=item["name"],
            gtin=item.get("gtin"),
            is_marked=item["is_marked"],
            rest=item["rest"],
            store_id=item["store_id"],
            sgtins=sgtins,
            measure_unit_code=item.get("measure_unit_code"),
            measure_unit_alias=item.get("measure_unit_alias"),
            is_allow_sale_in_parts=item.get("is_allow_sale_in_parts"),
        )

    tasks = [enrich_item(item) for item in nomenclature]
    results = await asyncio.gather(*tasks)
    return results