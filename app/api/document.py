from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.service.document_service import DocumentService
from app.service.user_service import OAuth2PasswordBearerWithCookie, UserService

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)

document_service = DocumentService()
user_service = UserService()
oauth2_scheme = OAuth2PasswordBearerWithCookie()


class DocumentCreateRequest(BaseModel):
    name: str


@router.get("/")
async def read_documents(offset: int = 0, limit: int = 25) -> Dict[str, Any]:
    """
    Возвращает список документов с пагинацией и общее количество.
    """
    docs = await document_service.get_documents_paginated(offset=offset, limit=limit)
    total = await document_service.get_document_count()
    return {"items": docs, "total": total}


@router.post("/create")
async def create_document(
    payload: DocumentCreateRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Создаёт новый документ. Требует авторизации и права на создание документов.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not user.get("can_create"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для создания документа")

    document_id = await document_service.create_document(name=payload.name, author=user["username"])
    return {"id": document_id}
