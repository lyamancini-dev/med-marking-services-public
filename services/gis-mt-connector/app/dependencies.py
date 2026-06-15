from fastapi import Depends
import httpx

import app.container
from app.services.auth_manager import AuthManager
from app.services.true_api_client import TrueApiClient
from app.services.saga_orchestrator import SagaOrchestrator


def get_signer_client() -> httpx.AsyncClient:
    return app.container.http_client


def get_auth_manager() -> AuthManager:
    return app.container.auth_manager


def get_api_client() -> TrueApiClient:
    return app.container.true_api_client


def get_saga_orchestrator() -> SagaOrchestrator:
    return app.container.saga_orchestrator