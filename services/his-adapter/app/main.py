import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from .database import engine, Base
from .config import API_V1_PREFIX
from .api.v1 import router as v1_router
from .engine.status_worker import status_polling_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Создаём таблицы на основе расширенных моделей
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # 2. Наполняем справочник единиц измерения стандартными кодами ОКЕИ
        res = conn.execute(text("SELECT COUNT(*) FROM SERVICE_MEASURE_UNIT"))
        if res.scalar() == 0:
            conn.execute(
                text("""
                    INSERT INTO SERVICE_MEASURE_UNIT (ID, CODE, NAME, ALIAS) VALUES
                    (796, '796', 'Штука', 'шт'),
                    (163, '163', 'Грамм', 'г'),
                    (112, '112', 'Миллилитр', 'мл'),
                    (778, '778', 'Упаковка', 'уп')
                """)
            )
            conn.commit()
            print("OKEI measure units loaded.")

        # 3. Загружаем справочник складов
        res = conn.execute(text("SELECT COUNT(*) FROM STORES"))
        if res.scalar() == 0:
            conn.execute(
                text("""
                    INSERT INTO STORES (ID, NAME) VALUES
                    (1, 'Центральный склад'),
                    (2, 'Кабинет косметологии 1'),
                    (3, 'Кабинет косметологии 2'),
                    (4, 'Процедурный кабинет'),
                    (5, 'Операционная'),
                    (6, 'Стоматологический кабинет')
                """)
            )
            conn.commit()
            print("Stores loaded.")

        # 4. Загружаем товары с поддержкой частичного списания
        res = conn.execute(text("SELECT COUNT(*) FROM SERVICES"))
        if res.scalar() == 0:
            conn.execute(
                text("""
                    INSERT INTO SERVICES (ID, NAME, GTIN, IS_MARKED, REST, STORE_ID, MEAUSEREUNITID, ISALLOWSALEINPARTS) VALUES
                    (1, 'Шприц 5 мл', NULL, 0, 100, 1, 796, 0),
                    (2, 'Спирт этиловый', NULL, 0, 500, 1, 112, 1),
                    (3, 'Бинт стерильный', NULL, 0, 200, 1, 796, 0),
                    (4, 'Эндопротез тазобедренный', '04601234567890', 1, 5, 1, 796, 0),
                    (5, 'Катетер уретральный', '04601234567891', 1, 3, 2, 796, 0),
                    (6, 'Мазь антисептическая (туба)', '04601234567892', 1, 10, 1, 163, 1),
                    (7, 'Маска хирургическая', NULL, 0, 100, 1, 796, 1)
                """)
            )
            conn.commit()
            print("Expanded nomenclature loaded.")

        # 5. Реестр КИ (SGTIN) — сохраняем данные для всех маркированных позиций
        res = conn.execute(text("SELECT COUNT(*) FROM SGTIN_REGISTRY"))
        if res.scalar() == 0:
            conn.execute(
                text("""
                    INSERT INTO SGTIN_REGISTRY (ID, SERVICE_ID, SGTIN, STATUS) VALUES
                    (1, 4, '010460123456789021serial1' || x'1d' || '93crypto', 'AVAILABLE'),
                    (2, 4, '010460123456789021serial2' || x'1d' || '93crypto', 'AVAILABLE'),
                    (3, 5, '010460123456789121cath001' || x'1d' || '93crypto', 'AVAILABLE'),
                    (4, 6, '010460123456789221tube001' || x'1d' || '93crypto', 'AVAILABLE'),
                    (5, 6, '010460123456789221tube002' || x'1d' || '93crypto', 'AVAILABLE')
                """)
            )
            conn.commit()
            print("Full SGTIN registry loaded.")

    # 6. Запуск фонового воркера для опроса статусов
    worker_thread = threading.Thread(
        target=status_polling_worker,
        args=(30,),
        daemon=True
    )
    worker_thread.start()

    yield


app = FastAPI(title="HIS Adapter (Mock)", lifespan=lifespan)
app.include_router(v1_router, prefix=API_V1_PREFIX)