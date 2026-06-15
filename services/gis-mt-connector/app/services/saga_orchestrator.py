import asyncio
import base64
import json
import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import httpx

from app.config import Settings
from app.models import Saga
from app.services.true_api_client import TrueApiClient
from app.schemas import WithdrawalRequest, WithdrawalProduct

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"CHECKED_OK", "CHECKED_NOT_OK", "CANCELLED", "PARSE_ERROR"}

def normalize_cis(raw_sgtin: str) -> str:
    """Нормализация КИ: возвращает исходную строку без изменений."""
    return raw_sgtin.strip()

def map_dropout_reason_to_action(reason: str) -> str:
    mapping = {
        "MEDICAL_USE": "MEDICAL_USE",
        "LOSS": "LOSS",
        "DEFECT": "DESTRUCTION",
        "EXPIRATION": "DESTRUCTION",
        "OWN_USE": "OWN_USE",
        "DESTRUCTION": "DESTRUCTION",
        "OTHER": "OTHER",
    }
    return mapping.get(reason, "OTHER")

class SagaOrchestrator:
    def __init__(self, settings: Settings, db_session_factory, api_client: TrueApiClient, signer_client: httpx.AsyncClient):
        self.settings = settings
        self.db_session_factory = db_session_factory
        self.api_client = api_client
        self.signer_client = signer_client

    async def start_write_off(self, request_data: dict) -> str:
        saga_id = str(uuid.uuid4())
        async with self.db_session_factory() as session:
            saga = Saga(saga_id=saga_id, status="PENDING")
            session.add(saga)
            await session.commit()
        asyncio.create_task(self._execute_saga(saga_id, request_data))
        return saga_id

    async def get_saga_status(self, saga_id: str) -> Optional[dict]:
        async with self.db_session_factory() as session:
            result = await session.execute(select(Saga).filter(Saga.saga_id == saga_id))
            saga = result.scalar_one_or_none()
            if not saga:
                return None
            errors = json.loads(saga.errors) if saga.errors else None
            return {
                "saga_id": saga.saga_id,
                "status": saga.status,
                "doc_id": saga.doc_id,
                "errors": errors,
            }

    async def _execute_saga(self, saga_id: str, request_data: dict):
        async with self.db_session_factory() as session:
            result = await session.execute(select(Saga).filter(Saga.saga_id == saga_id))
            saga = result.scalar_one_or_none()
            if not saga:
                return

        try:
            raw_sgtins = request_data.get("sntins", [])
            if not isinstance(raw_sgtins, list):
                raise ValueError("Поле 'sntins' должно быть списком КИ")
            if len(raw_sgtins) > 30_000:
                raise ValueError("Превышено максимальное количество КИ (30 000)")

            normalized_cis_list = [normalize_cis(cis) for cis in raw_sgtins if cis]
            if not normalized_cis_list:
                raise ValueError("Нет валидных КИ для отправки")

            dropout_reason = request_data.get("dropout_reason", "MEDICAL_USE")
            action = map_dropout_reason_to_action(dropout_reason)

            withdrawal = WithdrawalRequest(
                inn=self.settings.participant_inn,
                action=action,
                action_date=request_data["source_doc_date"],
                document_type=request_data.get("source_doc_type", "OTHER"),
                document_number=request_data["source_doc_num"],
                document_date=request_data["source_doc_date"],
                primary_document_custom_name=request_data.get("source_doc_name", "Акт списания"),
                products=[WithdrawalProduct(cis=cis) for cis in normalized_cis_list],
            )

            doc_content = withdrawal.dict()
            # !!! УДАЛЕНО поле productGroup — оно не нужно и не соответствует спецификации LK_RECEIPT !!!

            # Преобразуем даты
            if 'action_date' in doc_content and hasattr(doc_content['action_date'], 'isoformat'):
                doc_content['action_date'] = doc_content['action_date'].isoformat()
            if 'document_date' in doc_content and hasattr(doc_content['document_date'], 'isoformat'):
                doc_content['document_date'] = doc_content['document_date'].isoformat()

            json_str = json.dumps(doc_content, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')

            if len(json_bytes) > 30 * 1024 * 1024:
                raise ValueError("Размер документа превышает 30 Мбайт")

            sign_resp = await self.signer_client.post(
                self.settings.signer_url,
                json={"data": json_str, "detached": True}
            )
            if sign_resp.status_code != 200:
                raise RuntimeError(f"Ошибка при подписании: {sign_resp.status_code}")
            signature = sign_resp.json()["signature"]

            encoded_doc = base64.b64encode(json_bytes).decode('ascii')

            api_body = {
                "document_format": "MANUAL",
                "product_document": encoded_doc,
                "type": "LK_RECEIPT",
                "signature": signature,
            }

            logger.info(f"Sending to True API (productGroup in URL: {self.settings.product_group})")
            logger.debug(f"api_body keys: {list(api_body.keys())}")

            response = await self.api_client.create_document(api_body, self.settings.product_group)
            doc_id = response.get("id")
            if not doc_id:
                raise RuntimeError("Не удалось получить id документа от ГИС МТ")

            async with self.db_session_factory() as session:
                saga = await session.get(Saga, saga.id)
                if saga:
                    saga.doc_id = doc_id
                    saga.status = "SENT"
                    await session.commit()

            await self._poll_document(saga_id, doc_id)

        except Exception as e:
            logger.exception("Ошибка при выполнении саги %s", saga_id)
            async with self.db_session_factory() as session:
                saga_obj = await session.get(Saga, saga.id) if 'saga' in locals() else None
                if saga_obj:
                    saga_obj.status = "ERROR"
                    saga_obj.errors = json.dumps([str(e)])
                    await session.commit()

    async def _poll_document(self, saga_id: str, doc_id: str, max_retries: int = 30, interval: int = 5):
        async with self.db_session_factory() as session:
            for _ in range(max_retries):
                await asyncio.sleep(interval)
                try:
                    info = await self.api_client.get_doc_info(doc_id)
                    # Дополнительная защита: если вдруг info не словарь — пропускаем итерацию
                    if not isinstance(info, dict):
                        logger.warning(f"Неожиданный тип ответа get_doc_info: {type(info)}")
                        continue
                    status = info.get("status", "UNKNOWN")
                    result = await session.execute(select(Saga).filter(Saga.saga_id == saga_id))
                    saga = result.scalar_one_or_none()
                    if not saga:
                        return
                    saga.status = status
                    if status == "CHECKED_NOT_OK":
                        saga.errors = json.dumps(info.get("errors", []))
                    elif status == "CHECKED_OK":
                        saga.errors = None
                    await session.commit()
                    if status in TERMINAL_STATUSES:
                        logger.info("Сага %s завершена со статусом %s", saga_id, status)
                        return
                except Exception as e:
                    logger.error("Ошибка поллинга %s: %s", saga_id, e)
            result = await session.execute(select(Saga).filter(Saga.saga_id == saga_id))
            saga = result.scalar_one_or_none()
            if saga:
                saga.status = "TIMEOUT"
                saga.errors = json.dumps(["Превышено время ожидания статуса"])
                await session.commit()