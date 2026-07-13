import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import subprocess

from .document import document_api
from .task import task_api
from .user import user_api
from .database import db
from .config import config

if sys.platform == "win32":
    # psycopg в async-режиме не работает с ProactorEventLoop (дефолтный на Windows).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

FRONTEND_DIST_DIR = os.path.join(config.common.root, "frontend", "dist")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Открывает пул соединений с БД при старте и закрывает при остановке сервера."""
    await db.init()

    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "porcelain_archive.task_manager"],
        cwd=config.common.root,
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


app = FastAPI(title="Архив", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_api.router)
app.include_router(task_api.router)
app.include_router(user_api.router)

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
