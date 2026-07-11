#!/usr/bin/env bash
# Установка python/npm-зависимостей проекта (venv из requirements.txt,
# npm-пакеты для сборки frontend), плюс создание пустого шаблона config.ini
# в ~/.config/porcelain-archive (тот же путь, что run_porcelain_archive_server.py
# использует как запасной по умолчанию) и установка ARCHIVE_CONFIG_INI_PATH
# для текущего пользователя.
#
# Скрипт полностью работает без sudo и не ставит системные пакеты (git,
# git-lfs, python3-venv, Node.js/npm, PostgreSQL) - только проверяет их
# наличие и подсказывает команду, если чего-то не хватает. Полный список
# и точные команды установки - в README.md.
#
# Список python-пакетов (requirements.txt) собран по фактическим import'ам
# в каждом .py файле проекта (модули стандартной библиотеки и локальные
# файлы проекта - app, config, task, extract_pdf_blocks, generate_config -
# в список не входят, их устанавливать не нужно).
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
.venv/bin/pip list --format=columns | grep -iE "fastapi|uvicorn|websockets|multipart|pydantic|psycopg|aiofiles|bcrypt|pillow|pdfminer|colorama|docx" || true

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

echo "== Шаблон config.ini =="
CONFIG_DIR="$HOME/.config/porcelain-archive"
CONFIG_PATH="$CONFIG_DIR/config.ini"

mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_PATH" ]; then
    echo "$CONFIG_PATH уже существует, не трогаю."
else
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

echo "== Переменная окружения ARCHIVE_CONFIG_INI_PATH =="
ENV_LINE="export ARCHIVE_CONFIG_INI_PATH=\"$CONFIG_PATH\""
PROFILE_FILE="$HOME/.bashrc"

touch "$PROFILE_FILE"
# убираем прежнюю настройку этой переменной, если была - не плодим дубли
sed -i '/^export ARCHIVE_CONFIG_INI_PATH=/d' "$PROFILE_FILE"
echo "$ENV_LINE" >> "$PROFILE_FILE"
echo "Добавлено в $PROFILE_FILE: $ENV_LINE"

export ARCHIVE_CONFIG_INI_PATH="$CONFIG_PATH"
echo "В текущей сессии уже действует. Для новых сессий выполните: source $PROFILE_FILE"
