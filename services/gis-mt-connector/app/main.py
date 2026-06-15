from fastapi import FastAPI
import logging
from app.container import init_container, close_container
from app.api.v1.sagas import router as sagas_router
from app.database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GIS MT Connector")

@app.on_event("startup")
async def startup():
    try:
        await create_tables()
        logger.info("DB tables created, initializing container...")
        await init_container()
        logger.info("Container initialized successfully.")
    except Exception as e:
        logger.exception("Startup failed")
        raise

@app.on_event("shutdown")
async def shutdown():
    await close_container()

app.include_router(sagas_router)