from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- МОДЕЛИ ДЛЯ СОВМЕСТИМОСТИ С HIS ADAPTER ---

class WriteOffRequest(BaseModel):
    """
    Схема, приходящая от HIS Adapter.
    Сохраняем структуру для обратной совместимости.
    """
    sntins: List[str] = Field(..., description="Список полных КИ с криптохвостом")
    dropout_reason: str = Field("MEDICAL_USE", description="Код причины выбытия")
    source_doc_type: str = Field("OTHER", description="Тип документа (обычно OTHER)")
    source_doc_date: date = Field(..., description="Дата первичного документа")
    source_doc_num: str = Field(..., description="Номер первичного документа")
    source_doc_name: Optional[str] = Field("Акт списания", description="Наименование документа")

# --- НОВЫЕ МОДЕЛИ ДЛЯ ВНУТРЕННЕГО ИСПОЛЬЗОВАНИЯ (TRUE API: LK_RECEIPT) ---

class WithdrawalProduct(BaseModel):
    """Элемент массива 'products' для True API. Содержит только нормализованный КИ."""
    cis: str

class WithdrawalRequest(BaseModel):
    """
    Внутренняя схема для формирования финального JSON вывода из оборота.
    Полностью соответствует спецификации LK_RECEIPT для медицинских изделий.
    """
    inn: str = Field(..., description="ИНН организации-владельца")
    action: str = Field("MEDICAL_USE", description="Причина выбытия (MEDICAL_USE, LOSS, DESTRUCTION и др.)")
    action_date: date = Field(..., description="Дата фактического вывода")
    document_type: str = Field("OTHER", description="Тип первичного документа (например, OTHER)")
    document_number: str = Field(..., description="Номер акта")
    document_date: date = Field(..., description="Дата акта")
    primary_document_custom_name: str = Field(..., description="Обязательно при типе документа OTHER")
    products: List[WithdrawalProduct] = Field(..., description="Массив объектов с нормализованными КИ")
    # Поле productGroup добавляется отдельно в коде оркестратора, здесь не указываем

# --- МОДЕЛИ ОТВЕТОВ ---

class SagaResponse(BaseModel):
    saga_id: str
    status: str

class SagaStatusResponse(BaseModel):
    saga_id: str
    status: str
    doc_id: Optional[str] = None
    errors: Optional[List[str]] = None