from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from .documents_service import documents_service

router = APIRouter(tags=["documents"])


@router.get("/api/ceramic/documents/{document_id}/thumb")
async def document_thumb(document_id: int) -> Response:
    image = await documents_service.get_card_thumb(document_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Миниатюра недоступна")
    return Response(content=image, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
