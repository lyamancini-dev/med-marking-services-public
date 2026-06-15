from fastapi import APIRouter, Depends, HTTPException
from app.schemas import WriteOffRequest, SagaResponse, SagaStatusResponse
from app.services.saga_orchestrator import SagaOrchestrator
from app.dependencies import get_saga_orchestrator

router = APIRouter(prefix="/api/v1/sagas", tags=["sagas"])

@router.post("/write-off", response_model=SagaResponse)
async def create_write_off(
    request: WriteOffRequest,
    orchestrator: SagaOrchestrator = Depends(get_saga_orchestrator)
):
    saga_id = await orchestrator.start_write_off(request.dict())
    return SagaResponse(saga_id=saga_id, status="PENDING")

@router.get("/{saga_id}/status", response_model=SagaStatusResponse)
async def get_saga_status(
    saga_id: str,
    orchestrator: SagaOrchestrator = Depends(get_saga_orchestrator)
):
    status_data = await orchestrator.get_saga_status(saga_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Saga not found")
    return SagaStatusResponse(**status_data)