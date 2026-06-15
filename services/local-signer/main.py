"""
Локальный сервис подписания для ГИС МТ (КриптоПро CSP 5.0, утилита csptest).
Полностью адаптирован под сборку v5.0.12000 и боевой сертификат организации.
"""

import os
import tempfile
import subprocess
import base64
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Body, HTTPException

# ---------- Настройки ----------
SIGNER_HOST = os.getenv("SIGNER_HOST", "0.0.0.0")
SIGNER_PORT = int(os.getenv("SIGNER_PORT", "8003"))
CSPTEST_PATH = os.getenv("CSPTEST_PATH", r"C:\Program Files\Crypto Pro\CSP\csptest.exe")

CERT_THUMBPRINT = os.getenv("CERT_THUMBPRINT", "0000000000000000000000000000000000000000")
CERT_PIN = ""  # PIN-код отсутствует для данного контейнера

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("local-signer")

# ---------- Инициализация приложения (Lifespan) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Проверки окружения при старте сервиса."""
    if not os.path.exists(CSPTEST_PATH):
        logger.error(f"Критическая ошибка: csptest не найден по пути {CSPTEST_PATH}")
        raise RuntimeError(f"csptest не найден: {CSPTEST_PATH}")
    logger.info(f"Утилита csptest успешно обнаружена: {CSPTEST_PATH}")

    try:
        # Быстрый тест запуска утилиты
        proc = subprocess.run([CSPTEST_PATH, "-sfsign", "-help"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            logger.info("Проверка синтаксиса csptest пройдена успешно.")
    except Exception as e:
        logger.error(f"Не удалось запустить csptest: {e}")
        raise

    yield


app = FastAPI(title="local-signer-real", version="2.1.0", lifespan=lifespan)

# ---------- Вспомогательные функции ----------
def cleanup_temp_files(*files):
    """Безопасное удаление временных файлов."""
    for f in files:
        try:
            if os.path.exists(f):
                os.unlink(f)
        except OSError as e:
            logger.warning(f"Не удалось удалить временный файл {f}: {e}")

def sign_data(data: str, detached: bool) -> str:
    """
    Подписывает строку данных через csptest -sfsign -sign.
    Передает чистый отпечаток в -my и включает сертификат в тело подписи через -add.
    """
    # Шаг 1. Гигиена данных. Жестко убираем пробелы, табы и \r\n, которые могли прилететь по сети
    clean_data = data.strip()
    
    logger.info(f"DATA TO SIGN (repr): {repr(clean_data)}")
    logger.info(f"DATA LENGTH: {len(clean_data)} chars")

    # Шаг 2. Запись строго в бинарном режиме 'w+b'. 
    # Windows НЕ добавит свои системные переводы строк 0x0D 0x0A в конец.
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix=".txt") as f:
        f.write(clean_data.encode("utf-8"))
        input_path = f.name

    output_path = input_path + ".p7s"

    # Приводим отпечаток к чистому виду
    thumbprint_clean = CERT_THUMBPRINT.strip().lower()

    # Формируем команду строго под КриптоПро CSP 5.0
    cmd = [
        CSPTEST_PATH,
        "-sfsign", "-sign",
        "-in", input_path,
        "-out", output_path,
        "-my", thumbprint_clean,  # Передача чистого хэша
        "-add"                    # Внедрение сертификата (Attached signature)
    ]
    
    if detached:
        cmd.append("-detached")
    if CERT_PIN:
        cmd.extend(["-password", CERT_PIN])

    try:
        logger.info(f"Старт подписания. Контекст: detached={detached}, отпечаток={thumbprint_clean}")
        
        # Запуск процесса выполнения
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            logger.error(f"КриптоПро вернул ошибку выполнения: {err}")
            raise RuntimeError(f"Ошибка КриптоПро: {err}")

        if not os.path.exists(output_path):
            raise RuntimeError("Процесс завершился успешно, но файл подписи .p7s не был создан.")

        # Читаем бинарный файл результирующей подписи
        with open(output_path, "rb") as sig_file:
            sig_bytes = sig_file.read()
        logger.info(f"Подпись успешно создана. Размер: {len(sig_bytes)} байт.")

        # Кодируем в чистый Base64 (без переносов строк, критично для Честного Знака)
        b64 = base64.b64encode(sig_bytes).decode("ascii")
        return b64.replace("\n", "").replace("\r", "")

    except subprocess.TimeoutExpired:
        logger.error("Превышено время ожидания csptest. Возможно, контейнер заблокирован.")
        raise RuntimeError("Тайм-аут csptest. Проверьте ключевой носитель.")
    except Exception as e:
        logger.exception("Внутренняя ошибка в модуле sign_data")
        raise RuntimeError(str(e))
    finally:
        # Обязательно подчищаем за собой временные файлы на диске
        cleanup_temp_files(input_path, output_path)

# ---------- API Эндпоинты ----------
@app.post("/sign")
async def sign(payload: dict = Body(...)):
    data = payload.get("data")
    detached = payload.get("detached", False)

    if not data or not isinstance(data, str):
        raise HTTPException(status_code=400, detail="Поле 'data' обязательно и должно быть непустой строкой")
    if not isinstance(detached, bool):
        raise HTTPException(status_code=400, detail="Поле 'detached' должно быть логического типа (true/false)")

    try:
        signature_base64 = sign_data(data, detached)
        return {"signature": signature_base64}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "service": "local-signer-real", 
        "crypto_engine": "csptest v5.0",
        "active_thumbprint": CERT_THUMBPRINT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=SIGNER_HOST, port=SIGNER_PORT, log_level="info")