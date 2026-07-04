from typing import Dict, Any
from fastapi import APIRouter

from app.service.document_service import DocumentService

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)

document_service = DocumentService()

@router.get("/")
def read_documents(offset: int = 0, limit: int = 25) -> Dict[str, Any]:
    """
    Возвращает список документов с пагинацией и общее количество.
    """
    docs = document_service.get_documents_paginated(offset=offset, limit=limit)
    total = document_service.get_document_count()
    return {"items": docs, "total": total}
