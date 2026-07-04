import uuid
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2

# --- MOCK Хранилище сессий ---
# В реальном приложении здесь будет Redis или база данных
mock_sessions: Dict[str, str] = {}


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    Схема аутентификации, которая ищет токен сначала в cookie,
    а затем в заголовке Authorization.
    """
    async def __call__(self, request: Request) -> str | None:
        # 1. Проверяем cookie
        token = request.cookies.get("session_token")
        if token:
            return token
        
        return None


class UserService:
    """
    Сервис для бизнес-логики, связанной с пользователями и аутентификацией.
    Вся логика здесь - MOCK (заглушка).
    """

    def login(self, username: str, password: str) -> Optional[str]:
        """Вход по логину и паролю."""
        # Проверяем "правильность" логина и пароля
        if username == "admin" and password == "admin":
            # Создаем и "сохраняем" токен сессии
            session_token = str(uuid.uuid4())
            mock_sessions[session_token] = username
            return session_token
        return None

    def logout(self, token: str) -> bool:
        """Выход из сессии (удаление токена)."""
        if token in mock_sessions:
            del mock_sessions[token]
            return True
        return False

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе по токену."""
        username = mock_sessions.get(token)
        if username:
            return {"username": username, "email": f"{username}@example.com"}
        return None