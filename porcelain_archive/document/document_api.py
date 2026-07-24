from typing import Annotated, Dict, Any, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .document_service import DocumentService, BRANCH_STATUSES, OCR_QUALITIES
from porcelain_archive.user import OAuth2PasswordBearerWithCookie, UserService, role_at_least

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


async def _resolve_commit(branch_id: int, commit: Optional[str]) -> Optional[str]:
    """Возвращает переданный коммит, либо last_commit ветки, если он не указан явно."""
    return commit or await document_service.get_branch_last_commit(branch_id)


class DocumentCreateRequest(BaseModel):
    name: str


class SetVisibilityRequest(BaseModel):
    is_visible: bool


class RenameDocumentRequest(BaseModel):
    name: str


class DocumentPropertyEntry(BaseModel):
    property_id: int
    values: List[str]


class SetDocumentPropertiesRequest(BaseModel):
    properties: List[DocumentPropertyEntry]


class SetBranchStatusRequest(BaseModel):
    status: str


class BranchCommentRequest(BaseModel):
    text: str


class RemovePagesRequest(BaseModel):
    start: int
    end: int


class ResetTextRequest(BaseModel):
    start: int
    end: int


class RecognizeTextRequest(BaseModel):
    start: int
    end: int


@router.get("/")
async def read_documents(request: Request, offset: int = 0, limit: int = 25) -> Dict[str, Any]:
    """
    Возвращает список документов с пагинацией и общее количество.
    Скрытые документы видны только пользователю с правом create/review.
    """
    user_id = await _get_current_user_id(request)
    docs = await document_service.get_documents_paginated(offset=offset, limit=limit, user_id=user_id)
    total = await document_service.get_document_count(user_id=user_id)
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
    if not role_at_least(user.get("role"), "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для создания документа")

    document_id = await document_service.create_document(name=payload.name, author=user["username"], user_id=user["id"])
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
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"branch_id": branch_id}


@router.post("/{document_id}/visibility")
async def set_document_visibility(
    document_id: int,
    payload: SetVisibilityRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Изменяет видимость документа для обычных пользователей. Требует роли moderator+.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения видимости документа")

    success = await document_service.set_document_visibility(document_id, payload.is_visible)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    return {"is_visible": payload.is_visible}


@router.post("/{document_id}/rename")
async def rename_document(
    document_id: int,
    payload: RenameDocumentRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Переименовывает документ. Требует роли moderator+.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для переименования документа")

    success = await document_service.rename_document(document_id, payload.name)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    return {"name": payload.name}


@router.post("/{document_id}/delete")
async def delete_document(
    document_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Удаляет документ (soft delete: deleted=1). Требует роли moderator+.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для удаления документа")

    success = await document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    return {"deleted": True}


@router.get("/branches/")
async def read_branches(
    token: Annotated[str, Depends(oauth2_scheme)],
    offset: int = 0,
    limit: int = 25,
    branch_statuses: Annotated[Optional[List[str]], Query(alias="status")] = None,
) -> Dict[str, Any]:
    """
    Возвращает список наборов изменений с пагинацией. Требует авторизации.
    Пользователь с правом review видит все, остальные - только свои.
    branch_statuses (повторяющийся query-параметр "status") - опциональный
    фильтр по статусам набора изменений (любой из переданных).
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_list_available(user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Список наборов изменений недоступен")
    if branch_statuses:
        unknown = set(branch_statuses) - BRANCH_STATUSES
        if unknown:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неизвестный статус: '{unknown.pop()}'")

    sees_all = role_at_least(user.get("role"), "moderator")
    branches = await document_service.get_branches_paginated(
        user["id"], sees_all, offset=offset, limit=limit, statuses=branch_statuses
    )
    total = await document_service.get_branch_count(user["id"], sees_all, statuses=branch_statuses)
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


@router.post("/branches/{branch_id}/submit_for_review")
async def submit_branch_for_review(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Автор отправляет набор изменений на проверку: in_work -> to_review.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_author(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только автор может отправить набор изменений на проверку")

    try:
        await document_service.submit_branch_for_review(branch_id, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"status": "to_review"}


@router.post("/branches/{branch_id}/return_to_work")
async def return_branch_to_work(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Автор возвращает набор изменений в работу: to_review -> in_work.
    Из in_review автор вернуть уже не может - это делает модератор.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_author(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только автор может вернуть набор изменений в работу")

    try:
        await document_service.return_branch_to_work(branch_id, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"status": "in_work"}


@router.post("/branches/{branch_id}/delete")
async def delete_branch(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Автор удаляет набор изменений: in_work -> rejected.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_author(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только автор может удалить набор изменений")

    try:
        await document_service.delete_branch_draft(branch_id, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"status": "rejected"}


@router.post("/branches/{branch_id}/status")
async def set_branch_status(
    branch_id: int,
    payload: SetBranchStatusRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Устанавливает статус набора изменений напрямую. Требует роли moderator+.
    'accepted' выставить нельзя - только автоматически по результату слияния.
    'in_accept' запускает слияние ветки в master.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения статуса")

    try:
        await document_service.set_branch_status(branch_id, payload.status, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"status": payload.status}


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
    if not await document_service.is_branch_editable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Редактирование ветки недоступно")

    try:
        return await document_service.add_pages(branch_id=branch_id, files=files, position=position, user_id=user["id"])
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
    if not await document_service.is_branch_editable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Редактирование ветки недоступно")

    try:
        return await document_service.remove_pages(branch_id=branch_id, start=payload.start, end=payload.end, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/text")
async def set_text(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    file: UploadFile = File(...),
    position: int = Form(...),
    ocr_quality: str = Form(...),
) -> Dict[str, Any]:
    """
    Загружает PDF и ставит в очередь применение его текста к страницам ветки.
    Требует авторизации и доступа к редактированию ветки.

    :param position: Номер страницы, с которой начинается применение текста.
    :param ocr_quality: Качество распознавания ('high', 'low' или 'worst').
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_editable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Редактирование ветки недоступно")
    if ocr_quality not in OCR_QUALITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неизвестное качество распознавания: '{ocr_quality}'")

    try:
        return await document_service.set_text(
            branch_id=branch_id, file=file, position=position, ocr_quality=ocr_quality, user_id=user["id"]
        )
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
    if not await document_service.is_branch_editable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Редактирование ветки недоступно")

    try:
        return await document_service.reset_text(branch_id=branch_id, start=payload.start, end=payload.end, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/branches/{branch_id}/text/recognize")
async def recognize_text(
    branch_id: int,
    payload: RecognizeTextRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Ставит в очередь распознавание текста (OCR) на изображениях страниц ветки.
    Требует авторизации и доступа к редактированию ветки.

    :param payload.start: Первая страница диапазона.
    :param payload.end: Последняя страница диапазона.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_editable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Редактирование ветки недоступно")

    try:
        return await document_service.recognize_text(branch_id=branch_id, start=payload.start, end=payload.end, user_id=user["id"])
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


@router.get("/branches/{branch_id}/comments")
async def get_branch_comments(
    branch_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает комментарии ветки: автоматические записи об изменении статуса
    и текстовые комментарии пользователей. Master-ветка доступна всем, кому
    доступен документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    comments = await document_service.get_branch_comments(branch_id)
    return {"items": comments}


@router.post("/branches/{branch_id}/comments")
async def create_branch_comment(
    branch_id: int,
    payload: BranchCommentRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Добавляет свободный текстовый комментарий к ветке. Требует авторизации
    и доступа к просмотру ветки.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await document_service.is_branch_viewable(user["id"], branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Комментарий не может быть пустым")

    await document_service.add_branch_comment(branch_id, text, user["id"])
    return {"ok": True}


@router.get("/branches/{branch_id}/pages_hash")
async def get_branch_pages_hash(
    branch_id: int,
    request: Request,
    commit: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Возвращает image_hash и text_hash всех страниц указанного коммита ветки
    (по умолчанию - последнего). Master-ветка доступна всем, кому доступен
    документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    resolved_commit = await _resolve_commit(branch_id, commit)
    return await document_service.get_pages_hash(resolved_commit)


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


@router.get("/download/{document_id}")
async def download_document_zip(
    document_id: int,
    request: Request,
) -> Response:
    """
    Возвращает zip-архив исходных изображений документа (текущий коммит master).
    Если архив ещё не собран - запускает его формирование в фоне и отвечает 202;
    вызывающая сторона должна повторить запрос позже.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_document_available(user_id, document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    try:
        zip_bytes = await document_service.get_or_build_document_zip(document_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if zip_bytes is None:
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "processing"})

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="document_{document_id}_images.zip"'},
    )


@router.get("/{document_id}/branches")
async def read_document_branches(
    document_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
    offset: int = 0,
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Возвращает список наборов изменений конкретного документа. Требует роли moderator+.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра наборов изменений документа")

    branches = await document_service.get_branches_by_document_paginated(document_id, offset=offset, limit=limit)
    total = await document_service.get_branch_count_by_document(document_id)
    return {"items": branches, "total": total}


@router.get("/{document_id}/properties")
async def read_document_properties(
    document_id: int,
    request: Request,
) -> Dict[str, Any]:
    """
    Возвращает указатели документа (document_property). Доступность как у
    самого документа, видимые значения фильтруются внутри сервиса по роли.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_document_available(user_id, document_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

    properties = await document_service.get_document_properties(document_id, user_id)
    return {"items": properties}


@router.put("/{document_id}/properties")
async def set_document_properties(
    document_id: int,
    payload: SetDocumentPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Полностью заменяет набор указателей документа переданным (пакетное
    сохранение вкладки "Указатели"). Требует роли moderator+.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для изменения указателей документа")

    entries = [{"property_id": e.property_id, "values": e.values} for e in payload.properties]
    try:
        await document_service.set_document_properties(document_id, entries)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"ok": True}


@router.get("/branches/{branch_id}/pages/{page_index}/image")
async def get_branch_page_image(
    branch_id: int,
    page_index: int,
    request: Request,
    commit: Optional[str] = None,
) -> Response:
    """
    Возвращает изображение страницы указанного коммита ветки (по умолчанию -
    последнего). Master-ветка доступна всем, кому доступен документ, остальные
    ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    resolved_commit = await _resolve_commit(branch_id, commit)
    image, media_type = await document_service.get_page_image(resolved_commit, page_index)
    return Response(content=image, media_type=media_type)


@router.get("/branches/{branch_id}/pages/{page_index}/image/preview")
async def get_branch_page_image_preview(
    branch_id: int,
    page_index: int,
    request: Request,
    commit: Optional[str] = None,
) -> Response:
    """
    Возвращает превью изображения страницы указанного коммита ветки (по
    умолчанию - последнего). Master-ветка доступна всем, кому доступен документ,
    остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    resolved_commit = await _resolve_commit(branch_id, commit)
    image, media_type = await document_service.get_page_image_preview(resolved_commit, page_index)
    return Response(content=image, media_type=media_type)


@router.get("/branches/{branch_id}/pages/{page_index}/text")
async def get_branch_page_text(
    branch_id: int,
    page_index: int,
    request: Request,
    commit: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Возвращает текст страницы указанного коммита ветки (по умолчанию -
    последнего) - блоки/спаны из PDF, если он задан. Master-ветка доступна
    всем, кому доступен документ, остальные ветки - только автору/ревьюеру.
    """
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_viewable(user_id, branch_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра ветки")

    resolved_commit = await _resolve_commit(branch_id, commit)
    text = await document_service.get_page_text(resolved_commit, page_index)
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
