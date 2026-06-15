from fastapi import APIRouter
from .nomenclature import router as nomenclature_router
from .documents import router as documents_router
from .stores import router as stores_router

router = APIRouter()
router.include_router(nomenclature_router, tags=["nomenclature"])
router.include_router(documents_router, tags=["documents"])
router.include_router(stores_router, tags=["stores"])