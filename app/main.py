import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import subprocess

from app.api import document, task, user
from app.database import db
from app.service.document_service import DocumentService
from app.service.task_service import TaskService
from app.service.user_service import UserService
from config import config

if sys.platform == "win32":
    # psycopg в async-режиме не работает с ProactorEventLoop (дефолтный на Windows).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

UI_DIR = os.path.join(config.common.root, "ui")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Открывает пул соединений с БД при старте и закрывает при остановке сервера."""
    await db.init()

    process = subprocess.Popen(
        [sys.executable, "-u", f"{config.common.root}/task_manager.py"]
    )

    try:
        yield
    finally:
        process.terminate()
        try:
            await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
        await db.close()


document_service = DocumentService()
task_service = TaskService()
user_service = UserService()

app = FastAPI(title="Архив", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document.router)
app.include_router(task.router)
app.include_router(user.router)


@app.get("/", include_in_schema=False)
async def read_index():
    """Отдает главную страницу приложения."""
    return FileResponse(os.path.join(UI_DIR, "document_list.html"))


@app.get("/login", include_in_schema=False)
async def read_login_page():
    """Отдает страницу авторизации."""
    return FileResponse(os.path.join(UI_DIR, "login.html"))


async def _get_current_user_id(request: Request) -> "int | None":
    """Возвращает id пользователя по cookie сессии, либо None для анонима."""
    token = request.cookies.get("session_token")
    if not token:
        return None
    user = await user_service.get_user_by_token(token)
    return user["id"] if user else None


def _access_denied_response() -> FileResponse:
    """Страница с понятным сообщением вместо технической ошибки доступа."""
    return FileResponse(
        os.path.join(UI_DIR, "access_denied.html"), status_code=status.HTTP_404_NOT_FOUND
    )


@app.get("/tasks", include_in_schema=False)
async def read_task_list_page(request: Request):
    """Отдает страницу списка задач, если она доступна пользователю."""
    user_id = await _get_current_user_id(request)
    if not await task_service.is_task_list_available(user_id):
        return _access_denied_response()
    return FileResponse(os.path.join(UI_DIR, "task_list.html"))


@app.get("/branches", include_in_schema=False)
async def read_branch_list_page(request: Request):
    """Отдает страницу списка наборов изменений, если она доступна пользователю."""
    user_id = await _get_current_user_id(request)
    if not await document_service.is_branch_list_available(user_id):
        return _access_denied_response()
    return FileResponse(os.path.join(UI_DIR, "branch_list.html"))


@app.get("/users", include_in_schema=False)
async def read_user_list_page(request: Request):
    """Отдает страницу списка пользователей, если она доступна пользователю."""
    user_id = await _get_current_user_id(request)
    if not await user_service.is_user_list_available(user_id):
        return _access_denied_response()
    return FileResponse(os.path.join(UI_DIR, "user_list.html"))


@app.get("/document/{document_id}", include_in_schema=False)
async def read_document_page(document_id: int, request: Request):
    """Отдает страницу просмотра документа, если она доступна пользователю."""
    user_id = await _get_current_user_id(request)
    if not await document_service.is_document_available(user_id, document_id):
        return _access_denied_response()
    return FileResponse(os.path.join(UI_DIR, "document.html"))


@app.get("/edit/{branch_id}", include_in_schema=False)
async def read_edit_page(branch_id: int, request: Request):
    """Отдает страницу редактирования ветки, если она доступна пользователю."""
    user_id = await _get_current_user_id(request)
    if not await document_service.is_edit_available(user_id, branch_id):
        return _access_denied_response()
    return FileResponse(os.path.join(UI_DIR, "edit.html"))


# Должен быть последним - иначе перехватит запросы, предназначенные эндпоинтам выше.
app.mount("/static", StaticFiles(directory=UI_DIR, check_dir=False), name="ui-static")
