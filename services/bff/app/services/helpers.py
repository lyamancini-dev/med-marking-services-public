import logging
import time
from typing import Any, Dict

logger = logging.getLogger("bff")

async def log_request(method: str, url: str, status_code: int, duration: float):
    logger.info(f"{method} {url} -> {status_code} ({duration:.2f}s)")

class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail