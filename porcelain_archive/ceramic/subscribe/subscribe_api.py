from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Request, Response

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
async def list_subscribers(
    offset: int = 0, limit: int = 100, q: str = "", _: dict = Depends(require_role("admin"))
):
    return await subscribe_service.list_subscribers(offset, limit, q)


@router.get("/api/ceramic/subscribe/export")
async def export_subscribers(q: str = "", _: dict = Depends(require_role("admin"))) -> Response:
    """Выгрузка подписок в CSV (email, дата подписки)."""
    rows = await subscribe_service.all_emails(q)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["email", "подписан"])
    for row in rows:
        created = row["created_at"]
        writer.writerow([row["email"], created.strftime("%Y-%m-%d %H:%M") if created else ""])
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="subscribers.csv"'},
    )


@router.delete("/api/ceramic/subscribe/{subscriber_id}", status_code=204)
async def delete_subscriber(subscriber_id: int, _: dict = Depends(require_role("admin"))):
    if not await subscribe_service.delete_subscriber(subscriber_id):
        raise HTTPException(status_code=404, detail="Подписка не найдена")
