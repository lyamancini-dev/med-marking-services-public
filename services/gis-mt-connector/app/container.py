import httpx
import logging
from app.config import Settings
from app.services.auth_manager import AuthManager
from app.services.true_api_client import TrueApiClient
from app.services.saga_orchestrator import SagaOrchestrator
from app.database import async_session_factory

logger = logging.getLogger(__name__)

settings = Settings()

http_client: httpx.AsyncClient | None = None
auth_manager: AuthManager | None = None
true_api_client: TrueApiClient | None = None
saga_orchestrator: SagaOrchestrator | None = None

async def init_container():
    global http_client, auth_manager, true_api_client, saga_orchestrator
    try:
        http_client = httpx.AsyncClient()
        auth_manager = AuthManager(settings, http_client)
        true_api_client = TrueApiClient(settings, auth_manager)
        saga_orchestrator = SagaOrchestrator(
            settings,
            async_session_factory,
            true_api_client,
            http_client,
        )
        logger.info("Container initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize container")
        raise

async def close_container():
    if auth_manager:
        await auth_manager.close()
    if true_api_client:
        await true_api_client.close()
    if http_client:
        await http_client.aclose()