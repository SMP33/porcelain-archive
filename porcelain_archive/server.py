import asyncio
import os
import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import subprocess

from .document import document_api
from .task import task_api
from .task.task_service import TaskService
from .user import user_api
from .property import property_api
from .database import db
from .config import config

from .ceramic.feedback import feedback_api as ceramic_feedback_api
from .ceramic.search import search_api as ceramic_search_api
from .ceramic.user import user_api as ceramic_user_api
from .ceramic.site_api import router as ceramic_site_router
from .ceramic.security import security_middleware as ceramic_security_middleware
from .ceramic.database import db as ceramic_db

if sys.platform == "win32":
    # psycopg в async-режиме не работает с ProactorEventLoop (дефолтный на Windows).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

FRONTEND_DIST_DIR = os.path.join(config.common.root, "frontend", "dist")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")

task_service = TaskService()


async def _run_backup_scheduler() -> None:
    """Раз в config.common.backup_period_hr часов создаёт задачу бэкапа."""
    while True:
        await asyncio.sleep(config.common.backup_period_hr * 3600)
        try:
            await task_service.create_backup_task()
        except Exception:
            traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Открывает пул соединений с БД при старте и закрывает при остановке сервера."""
    await db.init()
    await ceramic_db.init()

    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "porcelain_archive.task_manager"],
        cwd=config.common.root,
    )

    backup_scheduler_task = asyncio.create_task(_run_backup_scheduler())

    try:
        yield
    finally:
        backup_scheduler_task.cancel()
        process.terminate()
        try:
            await asyncio.wait_for(asyncio.to_thread(process.wait), timeout=5)
        except asyncio.TimeoutError:
            process.kill()
        await db.close()
        await ceramic_db.close()


app = FastAPI(title="Архив", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(ceramic_security_middleware)

app.include_router(document_api.router)
app.include_router(task_api.router)
app.include_router(user_api.router)
app.include_router(property_api.router)

app.include_router(ceramic_search_api.router)
app.include_router(ceramic_user_api.router)
app.include_router(ceramic_feedback_api.router)
app.include_router(ceramic_site_router)

app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="frontend-assets")


# Должен быть последним - иначе перехватит запросы, предназначенные эндпоинтам выше.
# Отдаёт собранный SPA (frontend/dist): статику из public/ (favicon и т.п.) как есть,
# всё остальное - index.html, дальше маршрутизацией занимается vue-router на клиенте.
@app.get("/{full_path:path}", include_in_schema=False)
async def read_frontend(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("assets/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    dist_root = os.path.realpath(FRONTEND_DIST_DIR)
    candidate = os.path.realpath(os.path.join(dist_root, full_path))
    is_inside_dist = candidate == dist_root or candidate.startswith(dist_root + os.sep)
    if full_path and is_inside_dist and os.path.isfile(candidate):
        return FileResponse(candidate)

    return FileResponse(os.path.join(FRONTEND_DIST_DIR, "index.html"))
