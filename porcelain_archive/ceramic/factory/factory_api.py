from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from porcelain_archive.ceramic.user import require_role

from .factory_service import factory_service

router = APIRouter(prefix="/api/ceramic/factories", tags=["factories"])


@router.get("")
@router.get("/")
async def list_factories(offset: int = 0, limit: int = 50):
    return await factory_service.list_factories(offset, limit)


@router.get("/{factory_id}")
async def get_factory(factory_id: int):
    factory = await factory_service.get_factory(factory_id)
    if factory is None:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return factory


@router.get("/{factory_id}/documents")
async def factory_documents(factory_id: int, offset: int = 0, limit: int = 24):
    return await factory_service.list_documents(factory_id, offset, limit)


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_factory(
    name: str = Form(...),
    location: str = Form(default=""),
    founded: str = Form(default=""),
    closed: str = Form(default=""),
    notes: str = Form(default=""),
    cover: UploadFile | None = None,
    _: dict = Depends(require_role("admin")),
):
    factory_id = await factory_service.create_factory(
        {"name": name, "location": location, "founded": founded, "closed": closed, "notes": notes},
        cover,
    )
    return {"id": factory_id}


@router.put("/{factory_id}")
async def update_factory(
    factory_id: int,
    name: str = Form(...),
    location: str = Form(default=""),
    founded: str = Form(default=""),
    closed: str = Form(default=""),
    notes: str = Form(default=""),
    cover: UploadFile | None = None,
    _: dict = Depends(require_role("admin")),
):
    try:
        await factory_service.update_factory(
            factory_id,
            {"name": name, "location": location, "founded": founded, "closed": closed, "notes": notes},
            cover,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return {"ok": True}


@router.delete("/{factory_id}", status_code=204)
async def delete_factory(factory_id: int, _: dict = Depends(require_role("admin"))):
    await factory_service.delete_factory(factory_id)


@router.delete("/{factory_id}/cover", status_code=204)
async def delete_factory_cover(factory_id: int, _: dict = Depends(require_role("admin"))):
    await factory_service.delete_cover(factory_id)
