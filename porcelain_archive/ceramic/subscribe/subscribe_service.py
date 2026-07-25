from __future__ import annotations

import re
import time
from collections import defaultdict

from porcelain_archive.ceramic.database import db as ceramic_db

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# In-memory rate limiter: максимум 5 подписок / 10 минут на IP.
_times: dict[str, list[float]] = defaultdict(list)
_LIMIT = 5
_WINDOW = 600


def _allowed(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _times[ip] if now - t < _WINDOW]
    _times[ip] = recent
    if len(recent) >= _LIMIT:
        return False
    _times[ip].append(now)
    return True


class SubscribeService:
    async def subscribe(self, email: str, ip: str) -> None:
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise ValueError("invalid_email")
        if not _allowed(ip):
            raise ValueError("rate_limited")
        # Повторная подписка тем же email не создаёт дубликат и не считается ошибкой.
        await ceramic_db.execute_write(
            "INSERT INTO subscriber (email) VALUES (%s) ON CONFLICT (email) DO NOTHING",
            (email,),
        )

    async def list_subscribers(self, offset: int, limit: int) -> dict:
        total_row = await ceramic_db.execute_read_one("SELECT COUNT(*) AS n FROM subscriber")
        total = total_row["n"] if total_row else 0
        rows = await ceramic_db.execute_read(
            "SELECT id, email, created_at FROM subscriber ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return {"items": rows, "total": total}


subscribe_service = SubscribeService()
