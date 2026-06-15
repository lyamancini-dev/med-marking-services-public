from fastapi import APIRouter
from .inventory import router as inventory_router
from .operations import router as operations_router
from .dictionaries import router as dictionaries_router
from .documents import router as documents_router

router = APIRouter()
router.include_router(inventory_router, prefix="/api/v1")
router.include_router(operations_router, prefix="/api/v1")
router.include_router(dictionaries_router, prefix="/api/v1")
router.include_router(documents_router, prefix="/api/v1")