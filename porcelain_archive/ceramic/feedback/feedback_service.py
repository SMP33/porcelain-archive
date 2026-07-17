from __future__ import annotations

import re
import time
from collections import defaultdict

from porcelain_archive.database import db as porcelain_db

# Обратная связь хранится в общей с porcelain_archive таблице message
# (receiver_type='feedback'). Отметка "важное" - отдельная таблица
# important_feedback (наличие строки = отмечено важным).
_FEEDBACK_RECEIVER_TYPE = "feedback"

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


def _compose_text(name: str, email: str, message: str) -> str:
    """
    message.text не имеет отдельных колонок под имя/email отправителя (в
    отличие от старой ceramic-таблицы feedback) - отправитель обычно аноним
    (author_id NULL), поэтому имя/email сохраняются первой строкой текста.
    См. _parse_text - обратное разбирание при чтении.
    """
    header_parts = []
    name = name.strip()
    email = email.strip()
    if name:
        header_parts.append(name)
    if email:
        header_parts.append(f"<{email}>")
    header = " ".join(header_parts)
    return f"{header}\n\n{message}" if header else message


def _parse_text(text: str) -> tuple[str | None, str | None, str]:
    """Обратная операция к _compose_text. При несовпадении формата (например,
    сообщение создано не через _compose_text) возвращает весь текст как есть."""
    if "\n\n" not in text:
        return None, None, text
    header, _, body = text.partition("\n\n")
    match = re.match(r"^(.*?)(?:\s*<(.+)>)?$", header)
    if not match:
        return None, None, text
    name = (match.group(1) or "").strip() or None
    email = match.group(2)
    if name is None and email is None:
        return None, None, text
    return name, email, body


class FeedbackService:
    async def submit(self, name: str, email: str, message: str, ip: str, author_id: int | None) -> None:
        if not _feedback_allowed(ip):
            raise ValueError("rate_limited")
        text = _compose_text(name, email, message.strip())
        await porcelain_db.execute_write(
            "INSERT INTO message (author_id, receiver_type, text, is_read, create_time) VALUES (%s, %s, %s, 0, now())",
            (author_id, _FEEDBACK_RECEIVER_TYPE, text),
        )

    async def list_messages(self, offset: int, limit: int) -> dict:
        total_rows = await porcelain_db.execute_read(
            "SELECT COUNT(*) FROM message WHERE receiver_type = %s", (_FEEDBACK_RECEIVER_TYPE,)
        )
        total = total_rows[0][0] if total_rows else 0

        rows = await porcelain_db.execute_read(
            """
            SELECT m.id, m.text, m.is_read, m.create_time, m.author_id,
                   (imp.message_id IS NOT NULL) AS is_important
            FROM message m
            LEFT JOIN important_feedback imp ON imp.message_id = m.id
            WHERE m.receiver_type = %s
            ORDER BY m.is_read ASC, m.create_time DESC
            LIMIT %s OFFSET %s
            """,
            (_FEEDBACK_RECEIVER_TYPE, limit, offset),
        )

        items = []
        for msg_id, text, is_read, create_time, author_id, is_important in rows:
            name, email, body = _parse_text(text or "")
            items.append({
                "id": msg_id,
                "name": name,
                "email": email,
                "message": body,
                "is_read": bool(is_read),
                "is_important": bool(is_important),
                "created_at": create_time,
                "author_id": author_id,
            })
        return {"items": items, "total": total}

    async def update_status(self, message_id: int, is_read: bool | None, is_important: bool | None) -> None:
        if is_read is not None:
            await porcelain_db.execute_write(
                "UPDATE message SET is_read = %s WHERE id = %s AND receiver_type = %s",
                (1 if is_read else 0, message_id, _FEEDBACK_RECEIVER_TYPE),
            )
        if is_important is not None:
            if is_important:
                await porcelain_db.execute_write(
                    "INSERT INTO important_feedback (message_id) VALUES (%s) ON CONFLICT DO NOTHING",
                    (message_id,),
                )
            else:
                await porcelain_db.execute_write(
                    "DELETE FROM important_feedback WHERE message_id = %s", (message_id,)
                )

    async def unread_count(self) -> int:
        rows = await porcelain_db.execute_read(
            "SELECT COUNT(*) FROM message WHERE receiver_type = %s AND is_read = 0",
            (_FEEDBACK_RECEIVER_TYPE,),
        )
        return rows[0][0] if rows else 0


feedback_service = FeedbackService()
