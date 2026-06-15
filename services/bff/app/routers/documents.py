from fastapi import APIRouter, Depends, HTTPException, Query
from httpx import AsyncClient
from typing import Optional
from ..dependencies import get_http_client, get_his_adapter_url

router = APIRouter(tags=["documents"])


@router.get("/stores")
async def get_stores(
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
):
    """Проксирует список складов из HIS Adapter."""
    try:
        url = f"{his_url}/api/v1/stores"
        resp = await http_client.get(url, timeout=10.0)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"HIS Adapter error: {resp.text}")
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/documents/{doc_id}/approve")
async def approve_document(
    doc_id: int,
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
):
    """Проксирует утверждение документа в HIS Adapter."""
    try:
        url = f"{his_url}/api/v1/documents/{doc_id}/approve"
        resp = await http_client.post(url, timeout=30.0)
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text)
            raise HTTPException(status_code=resp.status_code, detail=detail)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/documents")
async def list_documents(
    store_id: Optional[int] = Query(None, description="Фильтр по складу"),
    limit: int = Query(50, description="Количество документов"),
    http_client: AsyncClient = Depends(get_http_client),
    his_url: str = Depends(get_his_adapter_url),
):
    """Проксирует список документов из HIS Adapter с фильтрацией и лимитом."""
    try:
        url = f"{his_url}/api/v1/documents"
        params = {}
        if store_id is not None:
            params["store_id"] = store_id
        params["limit"] = limit
        resp = await http_client.get(url, params=params, timeout=10.0)
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"HIS Adapter error: {resp.text}")
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))