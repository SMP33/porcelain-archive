from typing import Annotated, Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .property_service import PropertyService
from porcelain_archive.user import OAuth2PasswordBearerWithCookie, UserService, role_at_least

router = APIRouter(
    prefix="/api/properties",
    tags=["properties"],
)

property_service = PropertyService()
user_service = UserService()
oauth2_scheme = OAuth2PasswordBearerWithCookie()


class CreatePropertyRequest(BaseModel):
    tag: str
    title: str
    description: Optional[str] = None
    is_list: bool = False
    is_editable: bool = True
    is_visible: bool = False


class UpdatePropertyTitleRequest(BaseModel):
    title: str


class UpdatePropertyFlagsRequest(BaseModel):
    is_list: bool
    is_editable: bool
    is_visible: bool


class ReorderPropertiesRequest(BaseModel):
    ids: List[int]


class CreateEnumValueRequest(BaseModel):
    value: str


class UpdateEnumValueRequest(BaseModel):
    value: str


async def _require_moderator(token: str) -> Dict[str, Any]:
    """Проверяет авторизацию и роль moderator+ - вся страница "Указатели" только для них."""
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "moderator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для управления указателями")
    return user


async def _require_admin(token: str) -> Dict[str, Any]:
    """Создавать/удалять указатели и менять их флаги может только администратор."""
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав - требуется роль администратора")
    return user


@router.get("/")
async def read_properties(token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """Возвращает список указателей. Требует роли moderator+."""
    await _require_moderator(token)

    properties = await property_service.get_properties()
    return {"items": properties}


@router.post("/")
async def create_property(
    payload: CreatePropertyRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Создаёт новый указатель. Требует роли admin."""
    await _require_admin(token)

    try:
        property_id = await property_service.create_property(
            tag=payload.tag,
            title=payload.title,
            description=payload.description,
            is_list=payload.is_list,
            is_editable=payload.is_editable,
            is_visible=payload.is_visible,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"id": property_id}


@router.patch("/{property_id}/title")
async def update_property_title(
    property_id: int,
    payload: UpdatePropertyTitleRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Изменяет отображаемое имя указателя. Требует роли moderator+."""
    await _require_moderator(token)

    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Название не может быть пустым")

    try:
        updated = await property_service.update_property_title(property_id, title)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Указатель не найден")
    return {"ok": True}


@router.patch("/{property_id}/flags")
async def update_property_flags(
    property_id: int,
    payload: UpdatePropertyFlagsRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Изменяет флаги указателя (недоступно для системных). Требует роли admin."""
    await _require_admin(token)

    try:
        updated = await property_service.update_property_flags(
            property_id, payload.is_list, payload.is_editable, payload.is_visible
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Указатель не найден")
    return {"ok": True}


@router.post("/reorder")
async def reorder_properties(
    payload: ReorderPropertiesRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Задаёт порядок отображения указателей. Требует роли moderator+."""
    await _require_moderator(token)

    await property_service.reorder_properties(payload.ids)
    return {"ok": True}


@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Удаляет указатель. Требует роли admin."""
    await _require_admin(token)

    try:
        deleted = await property_service.delete_property(property_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Указатель не найден")
    return {"ok": True}


@router.get("/{property_id}/enum")
async def read_property_enum_values(
    property_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Возвращает допустимые значения указателя. Требует роли moderator+."""
    await _require_moderator(token)

    values = await property_service.get_property_enum_values(property_id)
    return {"items": values}


@router.post("/{property_id}/enum")
async def create_property_enum_value(
    property_id: int,
    payload: CreateEnumValueRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Добавляет допустимое значение указателя. Требует роли moderator+."""
    await _require_moderator(token)

    value = payload.value.strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Значение не может быть пустым")

    try:
        enum_id = await property_service.create_property_enum_value(property_id, value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"id": enum_id}


@router.patch("/enum/{enum_id}")
async def update_property_enum_value(
    enum_id: int,
    payload: UpdateEnumValueRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Переименовывает допустимое значение указателя. Требует роли moderator+."""
    await _require_moderator(token)

    value = payload.value.strip()
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Значение не может быть пустым")

    try:
        await property_service.update_property_enum_value(enum_id, value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"ok": True}


@router.delete("/enum/{enum_id}")
async def delete_property_enum_value(
    enum_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Удаляет допустимое значение указателя. Требует роли moderator+."""
    await _require_moderator(token)

    try:
        deleted = await property_service.delete_property_enum_value(enum_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Значение не найдено")
    return {"ok": True}
