from typing import Annotated, Dict, Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
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


async def _get_current_user_id(request: Request) -> Optional[int]:
    """Возвращает id пользователя по cookie сессии, либо None для анонима."""
    token = request.cookies.get("session_token")
    if not token:
        return None
    user = await user_service.get_user_by_token(token)
    return user["id"] if user else None


class DocumentCreateRequest(BaseModel):
    name: str


class RemovePagesRequest(BaseModel):
    start: int
    end: int


class ResetTextRequest(BaseModel):
    start: int
    end: int


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


@router.post("/{document_id}/create_branch")
async def create_branch(
    document_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Создаёт новую ветку изменений для документа. Требует авторизации.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    try:
        branch_id = await document_service.create_branch(user_id=user["id"], document_id=document_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    return {"branch_id": branch_id}


@router.get("/branches/")
async def read_branches(
    token: Annotated[str, Depends(oauth2_scheme)],
    offset: int = 0,
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Возвращает список наборов изменений с пагинацией. Требует авторизации.
    Пользователь с правом review видит все, остальные - только свои.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    can_review = bool(user.get("can_review"))
    branches = await document_service.get_branches_paginated(
        user["id"], can_review, offset=offset, limit=limit
    )
    total = await document_service.get_branch_count(user["id"], can_review)
    return {"items": branches, "total": total}


@router.get("/branches/{branch_id}")
async def read_branch(
    branch_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает информацию о ветке. Master-ветка доступна всем, кому доступен
    документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    branch = await document_service.get_branch_info(branch_id)
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ветка не найдена")

    return branch


@router.post("/branches/{branch_id}/merge")
async def merge_branch(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Ставит в очередь слияние ветки изменений в master. Требует прав review.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not user.get("can_review"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для применения изменений")

    try:
        return await document_service.merge_branch(branch_id=branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/pages")
async def add_pages(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    files: List[UploadFile] = File(...),
    position: int = Form(...),
) -> Dict[str, Any]:
    """
    Добавляет страницы (файлы изображений) в ветку изменений. Требует авторизации
    и доступа к редактированию ветки.

    :param position: Номер страницы, после которой вставлять (0 - в начало).
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_edit_available(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования ветки")

    try:
        return await document_service.add_pages(branch_id=branch_id, files=files, position=position)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/pages/remove")
async def remove_pages(
    branch_id: int,
    payload: RemovePagesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Удаляет диапазон страниц ветки. Требует авторизации и доступа к редактированию ветки.

    :param payload.start: Первая удаляемая страница.
    :param payload.end: Последняя удаляемая страница.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_edit_available(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования ветки")

    try:
        return await document_service.remove_pages(branch_id=branch_id, start=payload.start, end=payload.end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/text")
async def set_text(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    file: UploadFile = File(...),
    position: int = Form(...),
) -> Dict[str, Any]:
    """
    Загружает PDF и ставит в очередь применение его текста к страницам ветки.
    Требует авторизации и доступа к редактированию ветки.

    :param position: Номер страницы, с которой начинается применение текста.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_edit_available(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования ветки")

    try:
        return await document_service.set_text(branch_id=branch_id, file=file, position=position)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/text/reset")
async def reset_text(
    branch_id: int,
    payload: ResetTextRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Ставит в очередь удаление текста со страниц ветки. Требует авторизации
    и доступа к редактированию ветки.

    :param payload.start: Первая страница диапазона.
    :param payload.end: Последняя страница диапазона.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_edit_available(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для редактирования ветки")

    try:
        return await document_service.reset_text(branch_id=branch_id, start=payload.start, end=payload.end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/branches/{branch_id}/pages/count")
async def get_page_count(
    branch_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает количество страниц в ветке. Master-ветка доступна всем, кому
    доступен документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    count = await document_service.get_branch_page_count(branch_id)
    return {"count": count}


@router.get("/pages/allowed_extensions")
async def get_allowed_page_extensions() -> Dict[str, Any]:
    """
    Возвращает список расширений файлов, допустимых для страниц документа.
    """
    return {"extensions": document_service.get_allowed_page_extensions()}


@router.get("/{document_id}/master_branch_id")
async def get_master_branch_id(
    document_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает id основной (master) ветки документа. Требует доступа к документу.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_document_available(user_id, document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    branch_id = await document_service.get_master_branch_id(document_id)
    if branch_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ветка master не найдена")

    return {"branch_id": branch_id}


@router.get("/branches/{branch_id}/pages/{page_index}/image")
async def get_branch_page_image(
    branch_id: int,
    page_index: int,
    request: Request,
) -> Response:
    """
    Возвращает изображение страницы ветки. Master-ветка доступна всем, кому
    доступен документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    image, media_type = await document_service.get_branch_page_image(branch_id, page_index)
    return Response(content=image, media_type=media_type)


@router.get("/branches/{branch_id}/pages/{page_index}/image/preview")
async def get_branch_page_image_preview(
    branch_id: int,
    page_index: int,
    request: Request,
) -> Response:
    """
    Возвращает превью изображения страницы ветки. Master-ветка доступна всем, кому
    доступен документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    image, media_type = await document_service.get_branch_page_image_preview(branch_id, page_index)
    return Response(content=image, media_type=media_type)


@router.get("/branches/{branch_id}/pages/{page_index}/text")
async def get_branch_page_text(
    branch_id: int,
    page_index: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает текст страницы ветки (блоки/спаны из PDF), если он задан.
    Master-ветка доступна всем, кому доступен документ, остальные ветки -
    только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    text = await document_service.get_branch_page_text(branch_id, page_index)
    return {"text": text}


# Должен быть последним - иначе перехватит запросы, предназначенные более специфичным путям выше.
@router.get("/{document_id}")
async def read_document(
    document_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает информацию о документе. Требует доступа к документу.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_document_available(user_id, document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    document = await document_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    return document
