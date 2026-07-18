from typing import Annotated, Dict, Any
import psycopg
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from porcelain_archive.database import db
from .task_service import TaskService
from porcelain_archive.user import OAuth2PasswordBearerWithCookie, UserService, role_at_least

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
)

task_service = TaskService()
user_service = UserService()
oauth2_scheme = OAuth2PasswordBearerWithCookie()


@router.get("/")
async def read_tasks(
    token: Annotated[str, Depends(oauth2_scheme)],
    offset: int = 0,
    limit: int = 25,
) -> Dict[str, Any]:
    """
    Возвращает список задач с пагинацией и общее количество. Требует авторизации.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not await task_service.is_task_list_available(user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Список задач недоступен")

    tasks = await task_service.get_tasks_paginated(offset=offset, limit=limit)
    total = await task_service.get_task_count()
    return {"items": tasks, "total": total}


@router.get("/branch/{branch_id}")
async def read_tasks_by_branch(
    branch_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Возвращает задачи, относящиеся к указанной ветке. Требует авторизации.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    tasks = await task_service.get_tasks_by_branch_id(branch_id)
    return {"items": tasks}


@router.get("/{task_id}/log")
async def read_task_log(
    task_id: int,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Возвращает содержимое лог-файла задачи. Требует авторизации.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    log = await task_service.get_task_log(task_id)
    return {"log": log}


@router.get("/server-log")
async def read_server_log(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Dict[str, Any]:
    """
    Возвращает содержимое файла лога текущего запуска сервера. Требует роли admin.
    """
    user = await user_service.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")
    if not role_at_least(user.get("role"), "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для просмотра лога сервера")

    log = await task_service.get_server_log()
    return {"log": log}


@router.websocket("/ws")
async def task_updates_ws(websocket: WebSocket) -> None:
    """
    Пушит уведомления об изменениях таблицы task (LISTEN/NOTIFY канал
    task_changed) и статуса набора изменений (канал branch_changed), чтобы
    страница списка задач и страница редактирования набора изменений могли
    обновляться сами - в том числе у других пользователей, у которых открыта
    та же страница.
    """
    token = websocket.cookies.get("session_token")
    user = await user_service.get_user_by_token(token) if token else None
    if user is None:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    conn = await psycopg.AsyncConnection.connect(db.conninfo, autocommit=True)
    try:
        await conn.execute("LISTEN task_changed")
        await conn.execute("LISTEN branch_changed")
        async for notify in conn.notifies():
            if notify.channel == "branch_changed":
                await websocket.send_json({"branch_id": notify.payload})
            else:
                await websocket.send_json({"task_id": notify.payload})
    except WebSocketDisconnect:
        pass
    finally:
        await conn.close()
