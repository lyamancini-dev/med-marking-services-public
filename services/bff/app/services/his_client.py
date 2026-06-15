from httpx import AsyncClient
from typing import List, Dict, Any
from .helpers import log_request, ServiceError
import time

class HisAdapterClient:
    def __init__(self, client: AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def get_nomenclature(self, search: str = None, store_id: int = None) -> List[Dict]:
        url = f"{self.base_url}/api/v1/nomenclature"
        params = {}
        if search:
            params["search"] = search
        if store_id is not None:
            params["store_id"] = store_id
        start = time.monotonic()
        try:
            resp = await self.client.get(url, params=params, timeout=10.0)
        except Exception as e:
            raise ServiceError(503, f"HIS Adapter unavailable: {str(e)}")
        duration = time.monotonic() - start
        await log_request("GET", url, resp.status_code, duration)
        if resp.status_code >= 400:
            raise ServiceError(502, f"HIS Adapter error: {resp.text}")
        return resp.json()

    async def get_sgtins(self, service_id: int) -> List[Dict]:
        url = f"{self.base_url}/api/v1/nomenclature/{service_id}/sgtins"
        start = time.monotonic()
        try:
            resp = await self.client.get(url, timeout=10.0)
        except Exception as e:
            raise ServiceError(503, f"HIS Adapter unavailable: {str(e)}")
        duration = time.monotonic() - start
        await log_request("GET", url, resp.status_code, duration)
        if resp.status_code >= 400:
            raise ServiceError(502, f"HIS Adapter error: {resp.text}")
        return resp.json()

    async def create_draft(self, data: Dict) -> Dict:
        url = f"{self.base_url}/api/v1/documents/draft"
        start = time.monotonic()
        try:
            resp = await self.client.post(url, json=data, timeout=15.0)
        except Exception as e:
            raise ServiceError(503, f"HIS Adapter unavailable: {str(e)}")
        duration = time.monotonic() - start
        await log_request("POST", url, resp.status_code, duration)
        if resp.status_code >= 400:
            raise ServiceError(502, f"HIS Adapter error: {resp.text}")
        return resp.json()