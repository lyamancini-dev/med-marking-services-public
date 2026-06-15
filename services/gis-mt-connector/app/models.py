from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Saga(Base):
    __tablename__ = "sagas"

    id = Column(Integer, primary_key=True, index=True)
    saga_id = Column(String, unique=True, index=True)
    doc_id = Column(String, nullable=True)          # uuid документа в ГИС МТ
    status = Column(String, default="PENDING")      # PENDING, SENT, CHECKED_OK, CHECKED_NOT_OK, CANCELLED, ERROR
    errors = Column(String, nullable=True)          # JSON-строка с ошибками
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())