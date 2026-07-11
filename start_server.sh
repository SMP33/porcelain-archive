#!/usr/bin/env bash
# Запуск сервера (run_server.py) в фоне, вывод дублируется в консоль и в лог-файл.
# Если сервер уже запущен - перезапускает его.

set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".run"
PID_FILE="$RUN_DIR/server.pid"
LOG_FILE="$RUN_DIR/server.log"

mkdir -p "$RUN_DIR"

is_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

if is_running; then
    echo "Сервер уже запущен (PID $(cat "$PID_FILE")), перезапускаю..."
    "$(dirname "$0")/stop_server.sh"
fi

echo "Запуск сервера..."
# > >(tee -a ...) - процесс-подстановка, а не обычный pipe: тогда $! возьмёт
# PID именно python-процесса, а не tee (иначе stop_server.sh убивал бы не тот процесс).
python3 run_server.py > >(tee -a "$LOG_FILE") 2>&1 &
echo $! > "$PID_FILE"
disown

sleep 1
if is_running; then
    echo "Сервер запущен, PID $(cat "$PID_FILE"). Лог: $LOG_FILE"
else
    echo "Не удалось запустить сервер (вывод выше, также см. $LOG_FILE)." >&2
    rm -f "$PID_FILE"
    exit 1
fi
