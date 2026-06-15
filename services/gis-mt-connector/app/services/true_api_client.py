import asyncio
import time
import logging
import re
import httpx
from app.config import Settings
from app.services.auth_manager import AuthManager

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, rate: int):
        self.rate = rate
        self.tokens = rate
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.updated_at
            self.tokens = min(self.rate, self.tokens + time_passed * self.rate)
            self.updated_at = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                logger.debug("Rate limit: waiting %.2f seconds", wait)
                await asyncio.sleep(wait)
                self.tokens = 0
                self.updated_at = time.monotonic()
            else:
                self.tokens -= 1


class TrueApiClient:
    def __init__(self, settings: Settings, auth_manager: AuthManager):
        self.settings = settings
        self.base_url_v3 = settings.true_api_base_url.rstrip("/")
        self.base_url_v4 = settings.true_api_base_url_v4.rstrip("/")
        self.auth_manager = auth_manager
        self.http_client = auth_manager.http_client
        self.limiter = RateLimiter(settings.rate_limit_per_sec)

    async def _request(self, method: str, path: str, base_url: str = None, **kwargs) -> httpx.Response:
        await self.limiter.acquire()
        token = await self.auth_manager.get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        url = f"{base_url or self.base_url_v3}{path}"

        response = await self.http_client.request(method, url, headers=headers, **kwargs)

        if response.status_code == 400:
            logger.error(f"Response body (400): {response.text}")

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = int(retry_after) if retry_after else 30
            logger.warning("Rate limit exceeded, retrying after %d seconds", wait)
            await asyncio.sleep(wait)
            response = await self.http_client.request(method, url, headers=headers, **kwargs)
        return response

    async def create_document(self, body: dict, product_group: str) -> dict:
        url = f"/lk/documents/create?pg={product_group}"
        response = await self._request("POST", url, json=body)

        if response.status_code >= 400:
            logger.error(f"Create document failed with status {response.status_code}: {response.text}")
            raise httpx.HTTPStatusError(
                f"Create document failed: {response.status_code}",
                request=response.request,
                response=response,
            )

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response content: {response.text[:500]}")

        # True API возвращает 201 Created и в теле ответа UUID строкой (plain/text)
        if response.status_code == 201:
            doc_id = response.text.strip()
            if doc_id and len(doc_id) == 36:
                return {"id": doc_id}
            else:
                raise ValueError(f"Invalid document ID format: {doc_id}")

        if response.content:
            try:
                data = response.json()
                if "id" in data:
                    return data
            except Exception as e:
                logger.warning(f"Failed to parse JSON: {e}")

        location = response.headers.get("Location")
        if location:
            match = re.search(r'/([a-f0-9\-]+)$', location, re.IGNORECASE)
            if match:
                return {"id": match.group(1)}

        raise ValueError("No document ID in response from True API")

    async def get_doc_info(self, doc_id: str) -> dict:
        """Получает информацию о документе через API v4.
        В песочнице метод может вернуть список, даже для одного документа.
        Приводим к словарю, беря первый элемент."""
        url = f"/doc/{doc_id}/info"
        response = await self._request("GET", url, base_url=self.base_url_v4)
        if response.status_code != 200:
            logger.error(f"Get doc info failed: {response.status_code} - {response.text}")
            raise httpx.HTTPStatusError(
                f"Get doc info failed: {response.status_code}",
                request=response.request,
                response=response,
            )
        data = response.json()
        # Адаптация: если ответ — список, берём первый элемент (если есть)
        if isinstance(data, list):
            logger.warning(f"API вернул список вместо словаря, берём первый элемент. Длина списка: {len(data)}")
            if not data:
                return {}
            data = data[0]
        return data

    async def close(self):
        pass