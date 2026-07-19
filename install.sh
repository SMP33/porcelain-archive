#!/usr/bin/env bash
# Установка python/npm-зависимостей проекта (venv из requirements.txt,
# npm-пакеты для сборки frontend), плюс создание пустого шаблона config.ini
# в /usr/share/porcelain-archive (тот же путь, что модуль porcelain_archive
# использует по умолчанию на Linux). Создание файла требует sudo, так как
# каталог системный.
#
# Скрипт не ставит системные пакеты (git, git-lfs, python3-venv, Node.js/npm,
# PostgreSQL) - только проверяет их наличие и подсказывает команду, если
# чего-то не хватает. Полный список и точные команды установки - в README.md.
#
# Список python-пакетов (requirements.txt) собран по фактическим import'ам
# в каждом .py файле проекта (модули стандартной библиотеки и локальный
# пакет проекта - porcelain_archive - в список не входит, устанавливать
# его не нужно).
#
# Не включены зависимости abbyy_docx_extractor.py, специфичные для Windows
# (pythoncom, win32com - пакет pywin32) - на Linux этот скрипт всё равно
# не может работать, так как использует COM-автоматизацию MS Word.

set -euo pipefail

cd "$(dirname "$0")"

echo "== Проверка git =="
if ! command -v git >/dev/null 2>&1; then
    echo "git не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y git" >&2
    exit 1
fi

echo "== Проверка Git LFS =="
# git-lfs нужен как отдельный apt-пакет, иначе "git lfs ..." не существует
# как подкоманда git - именно это вызывает run_git(path, "lfs", "install", ...)
# в task/run_create_repos.py при создании репозитория документа.
if ! git lfs version >/dev/null 2>&1; then
    echo "git-lfs не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y git-lfs" >&2
    exit 1
fi
git lfs install

echo "== Проверка имени и почты git =="
# git commit падает с ошибкой, если user.name/user.email не заданы - для
# фоновых задач (git merge/commit в task/run_*.py) это блокирует всё.
# Реальные данные не нужны, важно лишь, что они не пустые.
if [ -z "$(git config --global user.name 2>/dev/null || true)" ]; then
    git config --global user.name "Archive Bot"
    echo "git config --global user.name не был задан, установлено значение по умолчанию: Archive Bot"
fi
if [ -z "$(git config --global user.email 2>/dev/null || true)" ]; then
    git config --global user.email "archive-bot@localhost"
    echo "git config --global user.email не был задан, установлено значение по умолчанию: archive-bot@localhost"
fi

echo "== Проверка Tesseract OCR =="
# Нужен для porcelain_archive/task/script/text_from_image.py (распознавание
# текста на изображениях страниц) - pytesseract сам по себе только обёртка
# над системным бинарником tesseract, языковой пакет rus ставится отдельно.
if ! command -v tesseract >/dev/null 2>&1; then
    echo "tesseract не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y tesseract-ocr tesseract-ocr-rus" >&2
    exit 1
fi
if ! tesseract --list-langs 2>&1 | grep -qx "rus"; then
    echo "Языковой пакет tesseract-ocr-rus не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y tesseract-ocr-rus" >&2
    exit 1
fi

echo "== Проверка python3 и модуля venv =="
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y python3" >&2
    exit 1
fi
if ! python3 -c "import venv" >/dev/null 2>&1; then
    echo "Модуль python3-venv не установлен. Установите его вручную (требует sudo):" >&2
    echo "  sudo apt-get install -y python3-venv python3-pip" >&2
    exit 1
fi

echo "== Создание venv (.venv) =="
if [ -d ".venv" ]; then
    echo ".venv уже существует, не пересоздаю."
else
    python3 -m venv .venv
fi

echo "== Установка python-зависимостей из requirements.txt =="
# Внутри venv pip - обычный самостоятельный pip (не dpkg-управляемый
# системный), поэтому его можно спокойно обновлять перед установкой.
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "== Готово =="
.venv/bin/pip list --format=columns | grep -iE "fastapi|uvicorn|websockets|multipart|pydantic|psycopg|aiofiles|bcrypt|pillow|pdfminer|colorama|docx|pytesseract" || true

echo "== Проверка Node.js/npm =="
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "Node.js/npm не установлены. Установите их вручную (требует sudo):" >&2
    echo "  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -" >&2
    echo "  sudo apt-get install -y nodejs" >&2
    exit 1
fi
echo "node $(node --version), npm $(npm --version) найдены."
# Установка npm-зависимостей и сборка frontend - в start.sh, он
# выполняется при каждом запуске и подхватывает актуальные исходники.

echo "== Шаблон config.ini (требует sudo) =="
CONFIG_DIR="/usr/share/porcelain-archive"
CONFIG_PATH="$CONFIG_DIR/config.ini"

sudo mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_PATH" ]; then
    echo "$CONFIG_PATH уже существует, не трогаю."
else
    sudo tee "$CONFIG_PATH" > /dev/null <<'EOF'
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
    # владелец - текущий пользователь, чтобы заполнять config.ini можно было без sudo
    sudo chown "$(id -u):$(id -g)" "$CONFIG_PATH"
    echo "Создан пустой шаблон $CONFIG_PATH - заполните значения перед запуском."
fi
