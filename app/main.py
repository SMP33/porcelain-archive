import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import document, user
from app.database import db 

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)
UI_DIR = os.path.join(PROJECT_DIR, 'ui')

db.init()

app = FastAPI(title="Архив")

# --- Настройка CORS ---
# Это позволит JavaScript-коду, запущенному в браузере,
# делать запросы к этому API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретный домен фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Подключение роутеров ---
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

# --- Обслуживание остальных статических файлов ---
# Этот обработчик должен идти после определения эндпоинтов, чтобы не перехватывать их.
app.mount("/static", StaticFiles(directory=UI_DIR, check_dir=False), name="ui-static")