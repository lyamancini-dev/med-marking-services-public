from fastapi import APIRouter
from typing import List
from ..schemas import DropoutReason

router = APIRouter(tags=["dictionaries"])

DROPOUT_REASONS = [
    DropoutReason(code="MEDICAL_USE", name="Использование для медицинского применения"),
    DropoutReason(code="OWN_USE", name="Использование для собственных нужд"),
    DropoutReason(code="DEFECT", name="Брак"),
    DropoutReason(code="EXPIRATION", name="Истечение срока годности"),
    DropoutReason(code="LOSS", name="Утрата"),
    DropoutReason(code="DESTRUCTION", name="Уничтожение"),
    DropoutReason(code="OTHER", name="Другое"),
]

@router.get("/dictionaries/dropout-reasons", response_model=List[DropoutReason])
async def get_dropout_reasons():
    return DROPOUT_REASONS