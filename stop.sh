#!/usr/bin/env bash
# Остановка сервера (start.sh или start_shared_dev.sh) и всех его процессов,
# включая дочерний task_manager - жёстко убивает всё с "porcelain_archive" в имени.

set -euo pipefail

cd "$(dirname "$0")"

if ! pgrep -f "porcelain_archive" > /dev/null 2>&1; then
    echo "Сервер не запущен."
    exit 0
fi

echo "Останавливаю все процессы porcelain_archive..."
pkill -9 -f "porcelain_archive" || true

sleep 0.5
if pgrep -f "porcelain_archive" > /dev/null 2>&1; then
    echo "Не удалось остановить все процессы." >&2
    exit 1
fi

echo "Сервер остановлен."
