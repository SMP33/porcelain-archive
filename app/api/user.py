from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.service.user_service import OAuth2PasswordBearerWithCookie, UserService

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearerWithCookie()
user_service = UserService()

@router.post("/login")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """Вход по логину и паролю, возвращает токен в cookie."""
    token = user_service.login(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Устанавливаем токен в httpOnly cookie для безопасности
    response.set_cookie(key="session_token", value=token, httponly=True)
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response, token: Annotated[str, Depends(oauth2_scheme)]):
    """Выход из системы."""
    user_service.logout(token)
    response.delete_cookie(key="session_token")
    return {"message": "Logout successful"}

@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    """Получение информации о текущем пользователе."""
    user = user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session token")
    return user