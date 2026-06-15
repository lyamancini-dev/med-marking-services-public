from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from .config import HIS_ADAPTER_URL, CONNECTOR_URL
from .routers import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        app.state.http_client = client
        app.state.his_adapter_url = HIS_ADAPTER_URL
        app.state.connector_url = CONNECTOR_URL
        yield

app = FastAPI(title="BFF", version="1.0.0", lifespan=lifespan)

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # локальный запуск фронтенда
        "http://127.0.0.1:3000",
        # при необходимости добавить IP сервера или домен
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bff"}