import threading
import time
import logging
import httpx
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import GisMtMetadata
from ..config import CONNECTOR_URL

# Настройка логирования для гарантированного вывода в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger("status-worker")

TERMINAL_STATUSES = {"CHECKED_OK", "CHECKED_NOT_OK", "TIMEOUT", "ERROR"}

def status_polling_worker(interval: int = 30):
    """Фоновый поток для синхронизации статусов из GIS-MT Connector."""
    print(f"Worker thread running, will check every {interval}s", flush=True)
    logger.info("Status polling worker loop started")

    while True:
        db: Session = SessionLocal()
        try:
            pending_docs = db.query(GisMtMetadata).filter(
                GisMtMetadata.gis_mt_status.in_(["SENT", "PENDING"]),
                GisMtMetadata.saga_id.isnot(None)
            ).all()

            if pending_docs:
                print(f"Worker: found {len(pending_docs)} pending document(s)", flush=True)
                logger.info("Found %d pending document(s)", len(pending_docs))

                with httpx.Client(timeout=10.0) as client:
                    for meta in pending_docs:
                        try:
                            url = f"{CONNECTOR_URL}/api/v1/sagas/{meta.saga_id}/status"
                            resp = client.get(url)
                            if resp.status_code == 200:
                                data = resp.json()
                                new_status = data.get("status")
                                if new_status and new_status != meta.gis_mt_status:
                                    print(f"Doc {meta.doc_id}: {meta.gis_mt_status} -> {new_status}", flush=True)
                                    logger.info("Doc %d: status changed %s -> %s", meta.doc_id, meta.gis_mt_status, new_status)
                                    meta.gis_mt_status = new_status
                                    if new_status in TERMINAL_STATUSES:
                                        errors = data.get("errors")
                                        if errors:
                                            meta.gis_mt_errors = str(errors)
                                    db.commit()
                            else:
                                logger.warning("Saga %s: HTTP %d", meta.saga_id, resp.status_code)
                        except Exception as e:
                            logger.error("Error polling saga %s: %s", meta.saga_id, str(e))
            else:
                # Раз в 5 циклов сообщим, что воркер жив
                if int(time.time()) % 150 < interval:
                    logger.debug("Worker alive, no pending docs")

        except Exception as e:
            logger.error("Worker critical error: %s", str(e))
        finally:
            db.close()

        time.sleep(interval)