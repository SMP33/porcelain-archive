#!/usr/bin/env bash
# Пересобирает frontend (npm install + npm run build) и запускает сервер
# в общедоступном тестовом режиме: слушает 0.0.0.0:80 напрямую, без nginx.
# Только для временного общего тестирования, не для постоянного продакшена.
#
# Порт 80 привилегированный - нужен root (sudo) либо CAP_NET_BIND_SERVICE
# на бинарнике python внутри .venv.

set -euo pipefail

cd "$(dirname "$0")"

HOST="0.0.0.0"
PORT="80"

RUN_DIR=".run"
LOG_FILE="$RUN_DIR/shared_dev.log"

mkdir -p "$RUN_DIR"

running_pids() {
    # Паттерн включает "--port 80", чтобы не задеть процесс, запущенный
    # обычным start.sh на порту 8000 (и наоборот).
    pgrep -f "porcelain_archive --host $HOST --port $PORT" || true
}

EXISTING_PIDS="$(running_pids)"
if [ -n "$EXISTING_PIDS" ]; then
    echo "Сервер уже запущен на $HOST:$PORT (PID: $EXISTING_PIDS), перезапускаю..."
    kill $EXISTING_PIDS 2>/dev/null || true
    sleep 1
    STILL_ALIVE="$(running_pids)"
    if [ -n "$STILL_ALIVE" ]; then
        kill -9 $STILL_ALIVE 2>/dev/null || true
    fi
fi

echo "Сборка frontend..."
npm --prefix frontend install
npm --prefix frontend run build

echo "Запуск сервера на $HOST:$PORT..."
.venv/bin/python3 -m porcelain_archive --host "$HOST" --port "$PORT" > >(tee -a "$LOG_FILE") 2>&1 &
disown

sleep 1
NEW_PIDS="$(running_pids)"
if [ -n "$NEW_PIDS" ]; then
    echo "Сервер запущен, PID: $NEW_PIDS. Лог: $LOG_FILE"
else
    echo "Не удалось запустить сервер (вывод выше, также см. $LOG_FILE)." >&2
    echo "Порт 80 привилегированный - возможно, нужен root/sudo." >&2
    exit 1
fi
