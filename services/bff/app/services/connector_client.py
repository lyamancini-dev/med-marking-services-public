from httpx import AsyncClient
from typing import Dict
from .helpers import log_request, ServiceError
import time

class ConnectorClient:
    def __init__(self, client: AsyncClient, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    async def start_write_off(self, data: Dict) -> Dict:
        url = f"{self.base_url}/api/v1/sagas/write-off"
        start = time.monotonic()
        try:
            resp = await self.client.post(url, json=data, timeout=15.0)
        except Exception as e:
            raise ServiceError(503, f"GIS MT Connector unavailable: {str(e)}")
        duration = time.monotonic() - start
        await log_request("POST", url, resp.status_code, duration)
        if resp.status_code >= 400:
            raise ServiceError(502, f"Connector error: {resp.text}")
        return resp.json()

    async def get_saga_status(self, saga_id: str) -> Dict:
        url = f"{self.base_url}/api/v1/sagas/{saga_id}/status"
        start = time.monotonic()
        try:
            resp = await self.client.get(url, timeout=10.0)
        except Exception as e:
            raise ServiceError(503, f"GIS MT Connector unavailable: {str(e)}")
        duration = time.monotonic() - start
        await log_request("GET", url, resp.status_code, duration)
        if resp.status_code >= 400:
            raise ServiceError(502, f"Connector error: {resp.text}")
        return resp.json()