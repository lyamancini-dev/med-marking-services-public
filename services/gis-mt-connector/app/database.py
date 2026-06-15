from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import Settings

settings = Settings()

# Асинхронный движок для SQLite
engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///"),
    echo=False,
)

async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def create_tables():
    """Создаёт все таблицы, описанные в моделях (при старте)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)