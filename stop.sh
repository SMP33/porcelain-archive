#!/usr/bin/env bash
# Остановка сервера, запущенного через start.sh.

set -euo pipefail

cd "$(dirname "$0")"

running_pids() {
    pgrep -f 'python3 run_porcelain_archive_server\.py' || true
}

PIDS="$(running_pids)"

if [ -z "$PIDS" ]; then
    echo "Сервер не запущен."
    exit 0
fi

echo "Останавливаю сервер (PID: $PIDS)..."
kill $PIDS 2>/dev/null || true

for _ in $(seq 1 20); do
    STILL_ALIVE="$(running_pids)"
    if [ -z "$STILL_ALIVE" ]; then
        echo "Сервер остановлен."
        exit 0
    fi
    sleep 0.5
done

echo "Сервер не остановился за 10с, завершаю принудительно (SIGKILL)..."
kill -9 $(running_pids) 2>/dev/null || true
