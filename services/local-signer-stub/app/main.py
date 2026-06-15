from fastapi import FastAPI, Body
import base64
import hashlib

app = FastAPI(title="local-signer-stub", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "local-signer-stub"}

@app.post("/sign")
async def sign(payload: dict = Body(...)):
    """
    Эмулирует подписание данных.
    Ожидает JSON:
    {
        "data": "строка для подписи",
        "detached": true|false  (необязательное, по умолчанию false)
    }
    Возвращает:
    {
        "signature": "base64-строка"
    }
    """
    data = payload["data"]
    detached = payload.get("detached", False)
    suffix = "detached" if detached else "attached"
    raw = f"{suffix}:{data}".encode()
    signature = base64.b64encode(hashlib.sha256(raw).digest()).decode()
    return {"signature": signature}