#!/usr/bin/env bash
# Остановка сервера, запущенного через start_server.sh.

set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".run"
PID_FILE="$RUN_DIR/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Сервер не запущен (файл $PID_FILE не найден)."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if ! kill -0 "$PID" 2>/dev/null; then
    echo "Процесс с PID $PID не найден, удаляю устаревший $PID_FILE."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Останавливаю сервер (PID $PID)..."
kill "$PID"

for _ in $(seq 1 20); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Сервер остановлен."
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 0.5
done

echo "Сервер не остановился за 10с, завершаю принудительно (SIGKILL)..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
