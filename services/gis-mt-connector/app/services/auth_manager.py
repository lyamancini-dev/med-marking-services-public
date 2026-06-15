import time
import httpx
import logging
from app.config import Settings

logger = logging.getLogger(__name__)

class AuthError(Exception):
    pass

class AuthManager:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self.settings = settings
        self.auth_url = settings.true_api_base_url.rstrip("/")
        self.oms_connection = settings.oms_connection
        self.http_client = http_client
        self.signer_url = settings.signer_url
        self.cache_seconds = settings.token_cache_seconds
        self._cached_token = None
        self._expires_at = 0.0

    async def get_token(self) -> str:
        now = time.monotonic()
        if self._cached_token and (now + 300) < self._expires_at:
            return self._cached_token

        key_url = f"{self.auth_url}/auth/key"
        key_resp = await self.http_client.get(key_url)
        logger.info(f"GET {key_url} -> {key_resp.status_code}")
        if key_resp.status_code != 200:
            raise AuthError(f"Failed /auth/key: {key_resp.status_code}")
        try:
            key_data = key_resp.json()
        except Exception:
            logger.exception("Failed to parse JSON from /auth/key")
            raise AuthError("Invalid JSON from /auth/key")
        uuid = key_data["uuid"]
        raw_data = key_data["data"]

        sign_resp = await self.http_client.post(
            self.signer_url,
            json={"data": raw_data, "detached": False}
        )
        if sign_resp.status_code != 200:
            raise AuthError(f"Local signer failed: {sign_resp.status_code}")
        signed_data = sign_resp.json()["signature"]

        # URL без oms_connection
        auth_url = f"{self.auth_url}/auth/simpleSignIn"
        payload = {
            "uuid": uuid,
            "data": signed_data,
            "inn": self.settings.participant_inn
        }
        logger.info(f"simpleSignIn payload: {payload}")

        auth_resp = await self.http_client.post(auth_url, json=payload)
        logger.info(f"POST {auth_url} -> {auth_resp.status_code}")
        if auth_resp.status_code != 200:
            logger.error(f"simpleSignIn response body: {auth_resp.text}")
            raise AuthError(f"Failed simpleSignIn: {auth_resp.status_code}")

        token_data = auth_resp.json()
        self._cached_token = token_data["token"]
        self._expires_at = time.monotonic() + self.cache_seconds
        logger.info("JWT token obtained successfully")
        return self._cached_token

    async def close(self):
        pass