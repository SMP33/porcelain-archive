#!/usr/bin/env bash
# Пересобирает frontend (npm install + npm run build) и запускает сервер
# (python -m porcelain_archive) в фоне, вывод дублируется в консоль и в лог-файл.
# Если сервер (или его дочерний task_manager, оставшийся висеть) уже запущен -
# останавливает все процессы porcelain_archive и запускает заново.
#
# Слушает 127.0.0.1:8000 (значения по умолчанию из porcelain_archive/__main__.py) -
# рассчитан на работу за reverse proxy (nginx и т.п.). Для временного публичного
# теста без nginx (0.0.0.0:80) используйте start_shared_dev.sh.

set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".run"
LOG_FILE="$RUN_DIR/server.log"

mkdir -p "$RUN_DIR"

if pgrep -f "porcelain_archive" > /dev/null 2>&1; then
    echo "Найдены запущенные процессы porcelain_archive, останавливаю..."
    pkill -9 -f "porcelain_archive" || true
    sleep 1
fi

echo "Сборка frontend..."
npm --prefix frontend install
npm --prefix frontend run build

echo "Запуск сервера..."
.venv/bin/python3 -m porcelain_archive > >(tee -a "$LOG_FILE") 2>&1 &
disown

sleep 1
NEW_PIDS="$(pgrep -f "porcelain_archive" || true)"
if [ -n "$NEW_PIDS" ]; then
    echo "Сервер запущен, PID: $NEW_PIDS. Лог: $LOG_FILE"
else
    echo "Не удалось запустить сервер (вывод выше, также см. $LOG_FILE)." >&2
    exit 1
fi
