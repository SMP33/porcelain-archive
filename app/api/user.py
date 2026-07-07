from typing import Annotated, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.service.user_service import OAuth2PasswordBearerWithCookie, UserService

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

oauth2_scheme = OAuth2PasswordBearerWithCookie()
user_service = UserService()


class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str


class SetDisplayNameRequest(BaseModel):
    display_name: str

@router.post("/login")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """Вход по логину и паролю, возвращает токен в cookie."""
    token = await user_service.login(form_data.username, form_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    response.set_cookie(key="session_token", value=token, httponly=True)
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response, token: Annotated[str, Depends(oauth2_scheme)]):
    """Выход из системы."""
    await user_service.logout(token)
    response.delete_cookie(key="session_token")
    return {"message": "Logout successful"}

@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(token: Annotated[str, Depends(oauth2_scheme)]):
    """Получение информации о текущем пользователе."""
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session token")
    return user

@router.post("/reset_password")
async def reset_password(
    payload: ResetPasswordRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Смена пароля текущего пользователя."""
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    success = await user_service.reset_password(user["id"], payload.old_password, payload.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль")
    return {"message": "Password updated"}

@router.post("/set_display_name")
async def set_display_name(
    payload: SetDisplayNameRequest,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """Изменение отображаемого имени (ФИО) текущего пользователя."""
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    await user_service.set_display_name(user["id"], payload.display_name)
    return {"message": "Display name updated", "display_name": payload.display_name}