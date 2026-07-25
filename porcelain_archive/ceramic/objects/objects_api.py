from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from porcelain_archive.ceramic.user import get_current_user, require_role

from .objects_service import objects_service

router = APIRouter(tags=["objects"])


class ReorderImagesRequest(BaseModel):
    image_ids: List[int]


async def _read_uploads(files: Optional[List[UploadFile]]) -> list[tuple[str, bytes]]:
    return [(f.filename or "", await f.read()) for f in (files or []) if f and f.filename]


@router.get("/api/ceramic/objects")
async def list_objects(
    q: str = "",
    pointer: List[int] = Query(default=[]),
    user: Optional[dict] = Depends(get_current_user),
):
    include_hidden = bool(user and user.get("role") == "admin")
    return {"items": await objects_service.list_objects(q, pointer, include_hidden)}


@router.get("/api/ceramic/objects/facets")
async def objects_facets():
    return {"properties": await objects_service.get_facets()}


@router.get("/api/ceramic/objects/pointers")
async def available_pointers(_: dict = Depends(require_role("admin"))):
    return {"properties": await objects_service.list_available_pointers()}


@router.get("/api/ceramic/objects/{object_id}")
async def get_object(object_id: int, user: Optional[dict] = Depends(get_current_user)):
    include_hidden = bool(user and user.get("role") == "admin")
    obj = await objects_service.get_object(object_id, include_hidden)
    if obj is None:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return obj


@router.post("/api/ceramic/objects", status_code=201)
async def create_object(
    name: str = Form(...),
    notes: str = Form(""),
    pointer: List[int] = Form(default=[]),
    is_visible: bool = Form(True),
    images: Optional[List[UploadFile]] = File(None),
    _: dict = Depends(require_role("admin")),
):
    try:
        object_id = await objects_service.create_object(
            name, notes, pointer, await _read_uploads(images), is_visible,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"id": object_id}


@router.put("/api/ceramic/objects/{object_id}")
async def update_object(
    object_id: int,
    name: str = Form(...),
    notes: str = Form(""),
    pointer: List[int] = Form(default=[]),
    is_visible: bool = Form(True),
    _: dict = Depends(require_role("admin")),
):
    try:
        ok = await objects_service.update_object(object_id, name, notes, pointer, is_visible)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return {"ok": True}


@router.delete("/api/ceramic/objects/{object_id}", status_code=204)
async def delete_object(object_id: int, _: dict = Depends(require_role("admin"))):
    ok = await objects_service.delete_object(object_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")


@router.post("/api/ceramic/objects/{object_id}/images", status_code=201)
async def add_images(
    object_id: int,
    images: List[UploadFile] = File(...),
    _: dict = Depends(require_role("admin")),
):
    try:
        result = await objects_service.add_images(object_id, await _read_uploads(images))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return {"images": result}


@router.delete("/api/ceramic/objects/{object_id}/images/{image_id}", status_code=204)
async def delete_image(object_id: int, image_id: int, _: dict = Depends(require_role("admin"))):
    ok = await objects_service.delete_image(object_id, image_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Фотография не найдена")


@router.put("/api/ceramic/objects/{object_id}/images/order")
async def reorder_images(
    object_id: int,
    payload: ReorderImagesRequest,
    _: dict = Depends(require_role("admin")),
):
    ok = await objects_service.reorder_images(object_id, payload.image_ids)
    if not ok:
        raise HTTPException(status_code=400, detail="Некорректный список фотографий")
    return {"ok": True}
