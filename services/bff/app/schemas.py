from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date


class InventoryItem(BaseModel):
    id: int
    name: str
    gtin: Optional[str] = None
    is_marked: int
    rest: float
    store_id: int
    sgtins: List[str] = []
    # Новые поля для единиц измерения и делимости
    measure_unit_code: Optional[str] = None
    measure_unit_alias: Optional[str] = None
    is_allow_sale_in_parts: Optional[int] = None


class WriteOffRow(BaseModel):
    service_id: int
    quantity: float
    sgtins: List[str] = []


class WriteOffRequest(BaseModel):
    store_from: int = Field(..., description="Склад-отправитель")
    store_to: int = Field(..., description="Склад-получатель (для перемещения) или 0 для списания")
    items: List[WriteOffRow]
    source_doc_date: date = Field(..., description="Дата документа акта списания (yyyy-MM-dd)")
    source_doc_num: Optional[str] = Field(None, description="Номер акта (если не указан, будет использован номер МИС)")
    dropout_reason: str = Field("MEDICAL_USE", description="Код причины выбытия из справочника")
    source_doc_type: str = Field("OTHER", description="Тип исходного документа (OTHER, DESTRUCTION_ACT, CUSTOMS_DECLARATION)")
    source_doc_name: Optional[str] = Field("Акт списания", description="Название документа")
    doctype_id: int = Field(2, description="Тип документа МИС (2 - списание)")


class WriteOffResponse(BaseModel):
    doc_id: int
    doc_number: str
    saga_id: Optional[str] = None
    saga_status: Optional[str] = None
    saga_errors: Optional[List[str]] = None


class DropoutReason(BaseModel):
    code: str
    name: str


class SagaStatusResponse(BaseModel):
    saga_id: str
    status: str
    doc_id: Optional[str] = None
    errors: Optional[List[str]] = None


class MoveRequest(BaseModel):
    store_from: int = Field(..., description="Склад-отправитель")
    store_to: int = Field(..., description="Склад-получатель")
    items: List[WriteOffRow]

    @validator('store_to')
    def store_to_must_differ(cls, v, values):
        if 'store_from' in values and v == values['store_from']:
            raise ValueError('Склад-получатель должен отличаться от склада-отправителя')
        if v == 0:
            raise ValueError('Склад-получатель не может быть 0 (перемещение)')
        return v

    @validator('items')
    def items_not_empty(cls, v):
        if not v:
            raise ValueError('Документ должен содержать хотя бы одну позицию')
        return v