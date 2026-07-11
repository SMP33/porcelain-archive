#!/usr/bin/env bash
# Установка зависимостей проекта на Ubuntu (python-пакеты в venv из
# requirements.txt, Node.js/npm для сборки frontend + PostgreSQL), плюс
# создание пустого шаблона config.ini в ~/.config/porcelain-archive (тот же
# путь, что run_porcelain_archive_server.py использует как запасной по
# умолчанию) и установка ARCHIVE_CONFIG_INI_PATH для текущего пользователя.
#
# Скрипт не использует sudo - команды, требующие системных привилегий
# (apt-get, systemctl), нужно выполнять из-под пользователя с уже имеющимися
# правами (например, из-под root или через "sudo bash install.sh" целиком).
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

echo "== Установка PostgreSQL =="
apt-get update
apt-get install -y postgresql postgresql-contrib
systemctl enable --now postgresql

echo "== Установка git + Git LFS =="
# git-lfs нужен как apt-пакет, иначе "git lfs ..." не существует как
# подкоманда git - именно это вызывает run_git(path, "lfs", "install", ...)
# в task/run_create_repos.py при создании репозитория документа.
apt-get install -y git git-lfs
git lfs install

echo "== Установка venv-пакета Python =="
apt-get install -y python3-venv python3-pip

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

echo "== Установка Node.js/npm =="
if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
else
    echo "node уже установлен ($(node --version)), пропускаю."
fi
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
