#!/usr/bin/env bash
# Пересобирает frontend (npm install + npm run build) и запускает сервер
# (python -m porcelain_archive) в фоне, вывод дублируется в консоль и в лог-файл.
# Если сервер уже запущен - перезапускает его.
#
# Слушает 127.0.0.1:8000 (значения по умолчанию из porcelain_archive/__main__.py) -
# рассчитан на работу за reverse proxy (nginx и т.п.). Для временного публичного
# теста без nginx (0.0.0.0:80) используйте start_shared_dev.sh.

set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".run"
LOG_FILE="$RUN_DIR/server.log"

mkdir -p "$RUN_DIR"

running_pids() {
    # Паттерн ищет подстроку "-m porcelain_archive" без "--port" - чтобы не
    # задеть процесс, запущенный start_shared_dev.sh на порту 80 (и наоборот).
    pgrep -f -- '-m porcelain_archive$' || true
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

echo "Сборка frontend..."
npm --prefix frontend install
npm --prefix frontend run build

echo "Запуск сервера..."
.venv/bin/python3 -m porcelain_archive > >(tee -a "$LOG_FILE") 2>&1 &
disown

sleep 1
NEW_PIDS="$(running_pids)"
if [ -n "$NEW_PIDS" ]; then
    echo "Сервер запущен, PID: $NEW_PIDS. Лог: $LOG_FILE"
else
    echo "Не удалось запустить сервер (вывод выше, также см. $LOG_FILE)." >&2
    exit 1
fi
