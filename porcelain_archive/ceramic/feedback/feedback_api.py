from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from porcelain_archive.ceramic.user import require_role
from porcelain_archive.ceramic.user.user_api import get_current_user

from .feedback_service import feedback_service

router = APIRouter(tags=["feedback"])


@router.post("/api/ceramic/feedback", status_code=201)
async def submit_feedback(request: Request):
    body = await request.json()
    message = str(body.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    ip = request.client.host if request.client else "unknown"
    # Форма анонимна, но если отправитель залогинен в ceramic - привязываем автора.
    current_user = await get_current_user(request)
    author_id = current_user["id"] if current_user else None
    try:
        await feedback_service.submit(str(body.get("name", "")), str(body.get("email", "")), message, ip, author_id)
    except ValueError:
        raise HTTPException(status_code=429, detail="Слишком много попыток. Попробуйте позже.")
    return {"ok": True}


@router.get("/api/ceramic/feedback")
async def list_feedback(offset: int = 0, limit: int = 50, _: dict = Depends(require_role("admin"))):
    return await feedback_service.list_messages(offset, limit)


@router.get("/api/ceramic/feedback/unread_count")
async def feedback_unread_count(_: dict = Depends(require_role("admin"))):
    return {"count": await feedback_service.unread_count()}


@router.patch("/api/ceramic/feedback/{message_id}")
async def update_feedback(message_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    await feedback_service.update_status(message_id, body.get("is_read"), body.get("is_important"))
    return {"ok": True}
