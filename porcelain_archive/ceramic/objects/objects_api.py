from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from porcelain_archive.ceramic.user import get_current_user

from .objects_service import objects_service

router = APIRouter(tags=["objects"])


@router.get("/api/ceramic/objects")
async def list_objects(
    q: str = "",
    pointer: List[str] = Query(default=[]),
    user: Optional[dict] = Depends(get_current_user),
):
    include_hidden = bool(user and user.get("role") == "admin")
    return {"items": await objects_service.list_objects(q, pointer, include_hidden)}


@router.get("/api/ceramic/objects/facets")
async def objects_facets():
    return {"properties": await objects_service.get_facets()}


@router.get("/api/ceramic/objects/{object_id}")
async def get_object(object_id: int, user: Optional[dict] = Depends(get_current_user)):
    include_hidden = bool(user and user.get("role") == "admin")
    obj = await objects_service.get_object(object_id, include_hidden)
    if obj is None:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return obj
