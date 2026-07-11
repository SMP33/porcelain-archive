#!/usr/bin/env bash
# Запуск сервера (run_porcelain_archive_server.py) в фоне, вывод дублируется в консоль и в лог-файл.
# Если сервер уже запущен - перезапускает его.

set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".run"
LOG_FILE="$RUN_DIR/server.log"

mkdir -p "$RUN_DIR"

running_pids() {
    pgrep -f 'python3 run_porcelain_archive_server\.py' || true
}

EXISTING_PIDS="$(running_pids)"
if [ -n "$EXISTING_PIDS" ]; then
    echo "Сервер уже запущен (PID: $EXISTING_PIDS), перезапускаю..."
    kill $EXISTING_PIDS 2>/dev/null || true
    sleep 1
    STILL_ALIVE="$(running_pids)"
    if [ -n "$STILL_ALIVE" ]; then
        kill -9 $STILL_ALIVE 2>/dev/null || true
    fi
fi

echo "Запуск сервера..."
python3 run_porcelain_archive_server.py > >(tee -a "$LOG_FILE") 2>&1 &
disown

sleep 1
NEW_PIDS="$(running_pids)"
if [ -n "$NEW_PIDS" ]; then
    echo "Сервер запущен, PID: $NEW_PIDS. Лог: $LOG_FILE"
else
    echo "Не удалось запустить сервер (вывод выше, также см. $LOG_FILE)." >&2
    exit 1
fi
