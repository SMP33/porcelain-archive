import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import subprocess

from app.api import document, user
from app.database import db

if sys.platform == "win32":
    # psycopg в async-режиме не работает с ProactorEventLoop (дефолтный на Windows).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)
UI_DIR = os.path.join(PROJECT_DIR, 'ui')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Открывает пул соединений с БД при старте и закрывает при остановке сервера."""
    await db.init()
        
    process = subprocess.Popen(
                    [sys.executable, "-u", f"task_manager/task_manager.py"]
                )
    
    yield
    
    await process.terminate()    
    await db.close()


app = FastAPI(title="Архив", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document.router)
app.include_router(user.router)

@app.get("/", include_in_schema=False)
async def read_index():
    """Отдает главную страницу приложения."""
    return FileResponse(os.path.join(UI_DIR, 'document_list.html'))

@app.get("/login", include_in_schema=False)
async def read_login_page():
    """Отдает страницу авторизации."""
    return FileResponse(os.path.join(UI_DIR, 'login.html'))

@app.get("/document/{document_id}", include_in_schema=False)
async def read_document_page(document_id: int):
    """Отдает страницу просмотра документа."""
    return FileResponse(os.path.join(UI_DIR, 'document.html'))

# Должен быть последним - иначе перехватит запросы, предназначенные эндпоинтам выше.
app.mount("/static", StaticFiles(directory=UI_DIR, check_dir=False), name="ui-static")