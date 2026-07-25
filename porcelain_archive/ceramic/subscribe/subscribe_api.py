from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from porcelain_archive.ceramic.user import require_role

from .subscribe_service import subscribe_service

router = APIRouter(tags=["subscribe"])


@router.post("/api/ceramic/subscribe", status_code=201)
async def subscribe(request: Request):
    body = await request.json()
    email = str(body.get("email", "")).strip()
    ip = request.client.host if request.client else "unknown"
    try:
        await subscribe_service.subscribe(email, ip)
    except ValueError as exc:
        if str(exc) == "rate_limited":
            raise HTTPException(status_code=429, detail="Слишком много попыток. Попробуйте позже.")
        raise HTTPException(status_code=400, detail="Введите корректный адрес электронной почты")
    return {"ok": True}


@router.get("/api/ceramic/subscribe")
async def list_subscribers(offset: int = 0, limit: int = 100, _: dict = Depends(require_role("admin"))):
    return await subscribe_service.list_subscribers(offset, limit)
