from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from porcelain_archive.config import config

from .user_service import ROLE_LEVELS, role_at_least, user_service

router = APIRouter(prefix="/api/ceramic/users", tags=["users"])

SESSION_COOKIE_NAME = "ceramic_session_token"
SESSION_MAX_AGE = 14 * 24 * 3600


async def get_current_user(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return await user_service.get_user_by_token(token)


async def require_user(request: Request) -> dict:
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user


def require_role(minimum: str):
    async def _dep(user: dict = Depends(require_user)) -> dict:
        if not role_at_least(user["role"], minimum):
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return user
    return _dep


@router.post("/login")
async def login(request: Request, response: Response):
    body = await request.json()
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    ip = request.client.host if request.client else "unknown"

    try:
        result = await user_service.login(username, password, ip)
    except ValueError as exc:
        if str(exc) == "blocked":
            raise HTTPException(
                status_code=429, detail="Слишком много неудачных попыток. Попробуйте через 15 минут."
            )
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    response.set_cookie(
        SESSION_COOKIE_NAME,
        result["token"],
        httponly=True,
        samesite="lax",
        secure=config.ceramicsite.app_env == "production",
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return result["user"]


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        await user_service.logout(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/me")
async def me(user: dict = Depends(require_user)):
    return user


@router.get("")
@router.get("/")
async def list_users(offset: int = 0, limit: int = 50, _: dict = Depends(require_role("admin"))):
    return await user_service.list_users(offset, limit)


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_user(request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    role = str(body.get("role", "contributor"))
    if not username or not password:
        raise HTTPException(status_code=400, detail="Укажите логин и пароль")
    try:
        await user_service.create_user(username, password, role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    return {"ok": True}


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, current: dict = Depends(require_role("admin"))):
    try:
        await user_service.delete_user(user_id, current["id"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Нельзя удалить свою учётную запись")


@router.put("/{user_id}/password")
async def change_password(user_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    password = str(body.get("password", "")).strip()
    if not password:
        raise HTTPException(status_code=400, detail="Пароль не может быть пустым")
    await user_service.change_password(user_id, password)
    return {"ok": True}
