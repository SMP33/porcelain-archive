from __future__ import annotations

import time
import uuid
from collections import defaultdict

import bcrypt
import psycopg

from porcelain_archive.database import db

# Роли, видимые ceramic-фронтенду. Общая таблица member хранит user/moderator/admin -
# member.user и member.moderator обе отображаются наружу как "contributor".
ROLE_LEVELS = {"contributor": 1, "admin": 2}

_CERAMIC_TO_MEMBER_ROLE = {"contributor": "user", "admin": "admin"}


def role_at_least(role: str | None, minimum: str) -> bool:
    return ROLE_LEVELS.get(role or "", 0) >= ROLE_LEVELS.get(minimum, 0)


def _member_role_to_ceramic(role: str | None) -> str:
    return "admin" if role == "admin" else "contributor"


# In-memory throttle по неудачным попыткам входа: 5 попыток / 15 минут на IP.
# Для многопроцессного деплоя нужен общий стор (Redis и т.п.).
_login_fails: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_FAILS = 5
_LOGIN_WINDOW = 900


def _login_blocked(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _login_fails[ip] if now - t < _LOGIN_WINDOW]
    _login_fails[ip] = recent
    return len(recent) >= _LOGIN_MAX_FAILS


def _record_login_fail(ip: str) -> None:
    _login_fails[ip].append(time.time())


def _reset_login_fails(ip: str) -> None:
    _login_fails.pop(ip, None)


class UserService:
    """
    Работает с общей таблицей member/session (см. porcelain_archive.user) -
    ceramic и porcelain используют один и тот же список пользователей.
    """

    async def login(self, username: str, password: str, ip: str) -> dict:
        """Возвращает {token, user}. Бросает ValueError('blocked'|'invalid')."""
        if _login_blocked(ip):
            raise ValueError("blocked")

        rows = await db.execute_read(
            "SELECT id, name, hash, role FROM member WHERE name = %s",
            (username,),
        )
        if not rows:
            _record_login_fail(ip)
            raise ValueError("invalid")

        user_id, name, password_hash, role = rows[0]
        if not password_hash or not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            _record_login_fail(ip)
            raise ValueError("invalid")

        _reset_login_fails(ip)
        token = uuid.uuid4().hex
        await db.execute_write(
            "INSERT INTO session (user_id, token) VALUES (%s, %s)",
            (user_id, token),
        )
        return {
            "token": token,
            "user": {"id": user_id, "username": name, "role": _member_role_to_ceramic(role)},
        }

    async def logout(self, token: str) -> None:
        await db.execute_write("UPDATE session SET is_active = 0 WHERE token = %s", (token,))

    async def get_user_by_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        rows = await db.execute_read(
            """
            SELECT m.id, m.name, m.role
            FROM session s
            JOIN member m ON m.id = s.user_id
            WHERE s.token = %s AND s.is_active = 1
            """,
            (token,),
        )
        if not rows:
            return None
        user_id, name, role = rows[0]
        return {"id": user_id, "username": name, "role": _member_role_to_ceramic(role)}

    async def list_users(self, offset: int, limit: int) -> dict:
        total_rows = await db.execute_read("SELECT COUNT(*) FROM member")
        total = total_rows[0][0] if total_rows else 0
        rows = await db.execute_read(
            "SELECT id, name, role, created_time FROM member ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        items = [
            {"id": r[0], "username": r[1], "role": _member_role_to_ceramic(r[2]), "created_at": r[3]}
            for r in rows
        ]
        return {"items": items, "total": total}

    async def create_user(self, username: str, password: str, role: str) -> None:
        if role not in ROLE_LEVELS:
            role = "contributor"
        member_role = _CERAMIC_TO_MEMBER_ROLE[role]
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            async with db.transaction() as conn:
                await conn.execute(
                    "INSERT INTO member (name, hash, role, created_time) VALUES (%s, %s, %s, now())",
                    (username.strip(), password_hash, member_role),
                )
        except psycopg.errors.UniqueViolation:
            raise ValueError("duplicate_username")

    async def delete_user(self, user_id: int, current_user_id: int) -> None:
        if user_id == current_user_id:
            raise ValueError("cannot_delete_self")
        await db.execute_write("DELETE FROM member WHERE id = %s", (user_id,))

    async def change_password(self, user_id: int, new_password: str) -> None:
        password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await db.execute_write("UPDATE member SET hash = %s WHERE id = %s", (password_hash, user_id))


user_service = UserService()
