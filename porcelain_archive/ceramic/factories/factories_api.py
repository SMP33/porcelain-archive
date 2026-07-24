from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from porcelain_archive.ceramic.user import require_role

from .factories_service import factories_service

router = APIRouter(tags=["factories"])


@router.get("/api/ceramic/factories")
async def list_factories():
    return {"items": await factories_service.list_factories()}


@router.get("/api/ceramic/factories/{factory_id}")
async def get_factory(factory_id: int, offset: int = 0, limit: int = Query(24, ge=1, le=100)):
    factory = await factories_service.get_factory(factory_id, offset, limit)
    if factory is None:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return factory


@router.post("/api/ceramic/factories", status_code=201)
async def create_factory(
    name: str = Form(...),
    location: str = Form(""),
    founded: str = Form(""),
    closed: str = Form(""),
    notes: str = Form(""),
    cover: Optional[UploadFile] = File(None),
    _: dict = Depends(require_role("admin")),
):
    cover_data = await cover.read() if cover else None
    try:
        factory_id = await factories_service.create_factory(
            name, location, founded, closed, notes,
            cover.filename if cover else None, cover_data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"id": factory_id}


@router.put("/api/ceramic/factories/{factory_id}")
async def update_factory(
    factory_id: int,
    name: str = Form(...),
    location: str = Form(""),
    founded: str = Form(""),
    closed: str = Form(""),
    notes: str = Form(""),
    remove_cover: bool = Form(False),
    cover: Optional[UploadFile] = File(None),
    _: dict = Depends(require_role("admin")),
):
    cover_data = await cover.read() if cover else None
    try:
        ok = await factories_service.update_factory(
            factory_id, name, location, founded, closed, notes,
            cover.filename if cover else None, cover_data, remove_cover,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return {"ok": True}


@router.delete("/api/ceramic/factories/{factory_id}", status_code=204)
async def delete_factory(factory_id: int, _: dict = Depends(require_role("admin"))):
    ok = await factories_service.delete_factory(factory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Объект не найден")
