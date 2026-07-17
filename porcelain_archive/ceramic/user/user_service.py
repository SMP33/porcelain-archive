from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from collections import defaultdict

from porcelain_archive.ceramic.database import db

ROLE_LEVELS = {"contributor": 1, "admin": 2}


def role_at_least(role: str | None, minimum: str) -> bool:
    return ROLE_LEVELS.get(role or "", 0) >= ROLE_LEVELS.get(minimum, 0)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"pbkdf2:{salt}:{h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split(":", 2)
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100_000
        ).hex() == h
    except Exception:
        return False


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
    async def ensure_default_admin(self, default_password: str) -> None:
        """Идемпотентно создаёт пользователя admin, если таблица users пуста."""
        row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM users")
        if row and row["cnt"] == 0:
            await db.execute_write(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ("admin", hash_password(default_password), "admin"),
            )

    async def login(self, username: str, password: str, ip: str) -> dict:
        """Возвращает {token, user}. Бросает ValueError('blocked'|'invalid')."""
        if _login_blocked(ip):
            raise ValueError("blocked")

        row = await db.execute_read_one(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,),
        )
        if not row or not verify_password(password, row["password_hash"]):
            _record_login_fail(ip)
            raise ValueError("invalid")

        _reset_login_fails(ip)
        token = uuid.uuid4().hex
        await db.execute_write(
            "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
            (token, row["id"]),
        )
        return {
            "token": token,
            "user": {"id": row["id"], "username": row["username"], "role": row["role"]},
        }

    async def logout(self, token: str) -> None:
        await db.execute_write(
            "UPDATE sessions SET is_active = false WHERE token = %s", (token,)
        )

    async def get_user_by_token(self, token: str | None) -> dict | None:
        if not token:
            return None
        return await db.execute_read_one(
            """
            SELECT u.id, u.username, u.role
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = %s AND s.is_active = true
            """,
            (token,),
        )

    async def list_users(self, offset: int, limit: int) -> dict:
        total_row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM users")
        items = await db.execute_read(
            "SELECT id, username, role, created_at FROM users ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return {"items": items, "total": total_row["cnt"] if total_row else 0}

    async def create_user(self, username: str, password: str, role: str) -> None:
        if role not in ROLE_LEVELS:
            role = "contributor"
        try:
            await db.execute_write(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username.strip(), hash_password(password), role),
            )
        except Exception:
            raise ValueError("duplicate_username")

    async def delete_user(self, user_id: int, current_user_id: int) -> None:
        if user_id == current_user_id:
            raise ValueError("cannot_delete_self")
        await db.execute_write("DELETE FROM users WHERE id = %s", (user_id,))

    async def change_password(self, user_id: int, new_password: str) -> None:
        await db.execute_write(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(new_password), user_id),
        )


user_service = UserService()
