#!/usr/bin/env bash
# Установка зависимостей проекта на Ubuntu (python-пакеты системным pip
# без venv + PostgreSQL), плюс создание пустого шаблона .secret/config.ini.
#
# Список python-пакетов собран по фактическим import'ам в каждом .py файле
# проекта (модули стандартной библиотеки и локальные файлы проекта - app,
# config, task, extract_pdf_blocks, generate_config - в список не входят,
# их устанавливать не нужно).
#
# Не включены зависимости abbyy_docx_extractor.py, специфичные для Windows
# (pythoncom, win32com - пакет pywin32) - на Linux этот скрипт всё равно
# не может работать, так как использует COM-автоматизацию MS Word.

set -euo pipefail

cd "$(dirname "$0")"

echo "== Установка PostgreSQL =="
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql

echo "== Проверка pip =="
if ! command -v pip3 >/dev/null 2>&1; then
    echo "pip3 не найден, устанавливаю через apt..."
    sudo apt-get install -y python3-pip
fi

python3 -m pip install --upgrade pip --break-system-packages

# --- app/, task/, task_manager.py, run_server.py, extract_pdf_blocks.py ---
PACKAGES=(
    "fastapi==0.138.2"          # app/api/*.py, app/main.py
    "uvicorn==0.49.0"           # run_server.py
    "websockets==16.0"          # ASGI-сервер: WebSocket для /api/tasks/ws (app/api/task.py)
    "python-multipart==0.0.32"  # FastAPI File(...)/Form(...) (app/api/document.py)
    "pydantic==2.13.4"          # app/api/*.py, task/info.py
    "psycopg[binary]==3.3.4"    # app/database/database.py, app/api/task.py, app/service/*.py, task/task_utils.py, task_manager.py
    "psycopg-pool==3.3.1"       # app/database/database.py
    "aiofiles==25.1.0"          # app/service/document_service.py
    "bcrypt==5.0.0"             # app/service/user_service.py
    "pillow==12.3.0"            # extract_pdf_blocks.py, task/task_utils.py
    "pdfminer.six==20260107"    # extract_pdf_blocks.py
    "colorama==0.4.6"           # extract_pdf_blocks.py (CLI-вывод)
    "python-docx==1.2.0"        # abbyy_docx_extractor.py (сам скрипт всё равно требует Windows COM)
)

echo "== Установка пакетов =="
python3 -m pip install --break-system-packages "${PACKAGES[@]}"

echo "== Готово =="
python3 -m pip list --format=columns | grep -iE "fastapi|uvicorn|websockets|multipart|pydantic|psycopg|aiofiles|bcrypt|pillow|pdfminer|colorama|docx" || true

echo "== Шаблон .secret/config.ini =="
CONFIG_PATH=".secret/config.ini"
if [ -f "$CONFIG_PATH" ]; then
    echo "$CONFIG_PATH уже существует, не трогаю."
else
    mkdir -p .secret
    cat > "$CONFIG_PATH" <<'EOF'
[Common]
root =

[Database]
host =
port =
dbname =
user =
password =

[Files]
repos_root =
repos_branch_root =
cache_path =
log_path =
EOF
    echo "Создан пустой шаблон $CONFIG_PATH - заполните значения перед запуском."
fi
