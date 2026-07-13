import uuid
from typing import Optional, Dict, Any, List

import bcrypt
import psycopg
from fastapi import Request
from fastapi.security import OAuth2

from ..database import db

# Порядок ролей (см. ROLES.md) - каждая следующая роль имеет все возможности предыдущей
ROLE_LEVELS = {"user": 1, "moderator": 2, "admin": 3}


def role_at_least(role: Optional[str], minimum: str) -> bool:
    """Проверяет, что роль пользователя не ниже minimum по иерархии ROLES.md."""
    if role is None:
        return False
    return ROLE_LEVELS.get(role, 0) >= ROLE_LEVELS[minimum]


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    Схема аутентификации, которая ищет токен в cookie
    """
    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get("session_token")
        if token:
            return token

        return None


class UserService:
    """
    Сервис для бизнес-логики, связанной с пользователями и аутентификацией.
    Пользователи и сессии хранятся в таблицах member/session.
    """

    async def login(self, username: str, password: str) -> Optional[str]:
        """Вход по логину и паролю. При успехе создаёт и возвращает session_token."""
        rows = await db.execute_read(
            "SELECT id, hash FROM member WHERE name = %s",
            (username,)
        )
        if not rows:
            return None

        user_id, password_hash = rows[0]
        if not password_hash or not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            return None

        session_token = str(uuid.uuid4())
        await db.execute_write(
            "INSERT INTO session (user_id, token) VALUES (%s, %s)",
            (user_id, session_token)
        )
        return session_token

    async def logout(self, token: str) -> bool:
        """Выход из сессии (деактивация токена)."""
        rows_affected = await db.execute_write(
            "UPDATE session SET is_active = 0 WHERE token = %s AND is_active = 1",
            (token,)
        )
        return rows_affected > 0

    async def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену активной сессии."""
        rows = await db.execute_read(
            """
            SELECT m.id, m.name, m.display_name, m.email, m.role
            FROM session s
            JOIN member m ON m.id = s.user_id
            WHERE s.token = %s AND s.is_active = 1
            """,
            (token,)
        )
        if not rows:
            return None

        user_id, name, display_name, email, role = rows[0]
        return {
            "id": user_id,
            "username": name,
            "display_name": display_name,
            "email": email,
            "role": role,
        }

    async def reset_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Меняет пароль пользователя после проверки старого пароля."""
        rows = await db.execute_read("SELECT hash FROM member WHERE id = %s", (user_id,))
        if not rows:
            return False

        password_hash = rows[0][0]
        if not password_hash or not bcrypt.checkpw(old_password.encode("utf-8"), password_hash.encode("utf-8")):
            return False

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        rows_affected = await db.execute_write(
            "UPDATE member SET hash = %s WHERE id = %s",
            (new_hash, user_id)
        )
        return rows_affected > 0

    async def set_display_name(self, user_id: int, display_name: str) -> bool:
        """Обновляет ФИО (display_name) пользователя."""
        rows_affected = await db.execute_write(
            "UPDATE member SET display_name = %s WHERE id = %s",
            (display_name, user_id)
        )
        return rows_affected > 0

    async def is_user_list_available(self, user_id: Optional[int]) -> bool:
        """
        Проверяет, доступен ли список пользователей указанному пользователю.
        Список виден только авторизованным пользователям.
        """
        return user_id is not None

    async def get_user_count(self) -> int:
        """Возвращает общее количество пользователей."""
        rows = await db.execute_read("SELECT COUNT(*) FROM member")
        return rows[0][0]

    async def get_users_paginated(self, offset: int = 0, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка пользователей для пагинации.

        :param offset: Смещение (сколько пользователей пропустить).
        :param limit: Количество пользователей для возврата.
        """
        rows = await db.execute_read(
            "SELECT id, name, display_name, email, role FROM member ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return [
            {
                "id": row[0],
                "username": row[1],
                "display_name": row[2],
                "email": row[3],
                "role": row[4],
            }
            for row in rows
        ]

    async def create_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "user",
    ) -> int:
        """
        Создаёт нового пользователя и возвращает его id.

        :param username: Логин (уникальный).
        :param password: Пароль (хешируется перед сохранением).
        :param role: Роль пользователя (см. ROLES.md): user, moderator или admin.
        """
        if not username or not password:
            raise ValueError("Логин и пароль обязательны")

        if role not in ROLE_LEVELS:
            raise ValueError(f"Неизвестная роль: '{role}'")

        rows = await db.execute_read("SELECT id FROM member WHERE name = %s", (username,))
        if rows:
            raise ValueError(f"Пользователь '{username}' уже существует")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        try:
            async with db.transaction() as conn:
                cursor = await conn.execute(
                    """
                    INSERT INTO member (name, display_name, email, hash, role)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (username, display_name, email, password_hash, role),
                )
                row = await cursor.fetchone()
        except psycopg.errors.UniqueViolation as exc:
            raise ValueError(f"Логин или email уже используются: {exc}") from exc

        return row[0]
