from pydantic import BaseModel
from typing import Optional, List
from datetime import date


# 1. СХЕМЫ НОМЕНКЛАТУРЫ

class NomenclatureItem(BaseModel):
    id: int
    name: str
    gtin: Optional[str] = None
    is_marked: int
    rest: float
    store_id: int
    # Новые поля для фронтенда (единицы измерения и делимость)
    measure_unit_code: Optional[str] = None
    measure_unit_alias: Optional[str] = None
    is_allow_sale_in_parts: Optional[int] = None

    class Config:
        from_attributes = True


class SgtinItem(BaseModel):
    sgtin: str


# 2. СХЕМЫ ОПЕРАЦИЙ

class DocumentRowCreate(BaseModel):
    service_id: int
    quantity: float
    sgtins: List[SgtinItem] = []


class DocumentCreate(BaseModel):
    doctype_id: int  # 2 – списание, 3 – перемещение
    store_from: int
    store_to: int
    items: List[DocumentRowCreate]
    # Метаданные ГИС МТ – обязательны только для списания (doctype_id=2)
    dropout_reason: Optional[str] = None
    source_doc_type: Optional[str] = "OTHER"
    source_doc_date: Optional[date] = None
    source_doc_num: Optional[str] = None
    source_doc_name: Optional[str] = "Акт списания"


class DocumentResponse(BaseModel):
    id: int
    doctype_id: int
    number: str
    date_fact: int
    is_close: int
    store_from: int
    store_to: int
    items: List[DocumentRowCreate]

    class Config:
        from_attributes = True



# 3. МОНИТОРИНГ (СПИСОК ДОКУМЕНТОВ)


class DocumentListItem(BaseModel):
    id: int
    doctype_id: int
    number: str
    date_fact: int
    is_close: int
    store_from: int
    store_to: int
    saga_id: Optional[str] = None
    gis_mt_status: Optional[str] = None
    gis_mt_errors: Optional[str] = None

    class Config:
        from_attributes = True