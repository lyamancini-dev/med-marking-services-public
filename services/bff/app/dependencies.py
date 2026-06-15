from httpx import AsyncClient
from fastapi import Request

async def get_http_client(request: Request) -> AsyncClient:
    return request.app.state.http_client

def get_his_adapter_url(request: Request) -> str:
    return request.app.state.his_adapter_url

def get_connector_url(request: Request) -> str:
    return request.app.state.connector_url