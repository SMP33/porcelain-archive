from __future__ import annotations

import re
import time
from collections import defaultdict

from porcelain_archive.ceramic.database import db

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# In-memory rate limiter: максимум 3 сообщения / 10 минут на IP.
# Для многопроцессного деплоя нужен общий стор.
_feedback_times: dict[str, list[float]] = defaultdict(list)
_FEEDBACK_LIMIT = 3
_FEEDBACK_WINDOW = 600


def _feedback_allowed(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _feedback_times[ip] if now - t < _FEEDBACK_WINDOW]
    _feedback_times[ip] = recent
    if len(recent) >= _FEEDBACK_LIMIT:
        return False
    _feedback_times[ip].append(now)
    return True


class FeedbackService:
    async def submit(self, name: str, email: str, message: str, ip: str) -> None:
        if not _feedback_allowed(ip):
            raise ValueError("rate_limited")
        await db.execute_write(
            "INSERT INTO feedback (name, email, message) VALUES (%s, %s, %s)",
            (name.strip() or None, email.strip() or None, message.strip()),
        )

    async def list_messages(self, offset: int, limit: int) -> dict:
        total_row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM feedback")
        items = await db.execute_read(
            "SELECT * FROM feedback ORDER BY is_read ASC, created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return {"items": items, "total": total_row["cnt"] if total_row else 0}

    async def update_status(self, message_id: int, is_read: bool | None, is_important: bool | None) -> None:
        if is_read is not None:
            await db.execute_write(
                "UPDATE feedback SET is_read = %s WHERE id = %s", (is_read, message_id)
            )
        if is_important is not None:
            await db.execute_write(
                "UPDATE feedback SET is_important = %s WHERE id = %s", (is_important, message_id)
            )

    async def unread_count(self) -> int:
        row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM feedback WHERE is_read = false")
        return row["cnt"] if row else 0

    async def subscribe(self, email: str) -> None:
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise ValueError("invalid_email")
        await db.execute_write(
            "INSERT INTO subscribers (email) VALUES (%s) ON CONFLICT (lower(email)) DO NOTHING",
            (email,),
        )

    async def list_subscribers(self, offset: int, limit: int) -> dict:
        total_row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM subscribers")
        items = await db.execute_read(
            "SELECT * FROM subscribers ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return {"items": items, "total": total_row["cnt"] if total_row else 0}

    async def delete_subscriber(self, subscriber_id: int) -> None:
        await db.execute_write("DELETE FROM subscribers WHERE id = %s", (subscriber_id,))


feedback_service = FeedbackService()
