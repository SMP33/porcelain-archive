import asyncio
import configparser
import os
import subprocess
import sys
import traceback
from pathlib import Path
import json
import psycopg
from typing import TypedDict
from task_info import TaskInfo

if sys.platform == "win32":
    # psycopg в async-режиме не работает с ProactorEventLoop (дефолтный на Windows).
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TASK_MANAGER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TASK_MANAGER_DIR)
TASKS_FOLDER = f"{TASK_MANAGER_DIR}/tasks"

NOTIFY_CHANNEL = "new_task"

SUPPORTED_TASK_TYPES = set()

for file in list(Path(TASKS_FOLDER).glob("*.py")):
    SUPPORTED_TASK_TYPES.add(Path(file).stem)
print(f"Доступные задачи: {SUPPORTED_TASK_TYPES}")

class TaskManager:
    """
    Слушает уведомления БД (LISTEN/NOTIFY) о новых документах и запускает
    repos_worker.py в отдельном процессе для каждого document_id.

    Воркеры выполняются строго по одному: если во время работы текущего
    воркера появляется новый документ, его id ставится в очередь и
    обрабатывается только после завершения текущего воркера.
    """

    def __init__(self):

        config = configparser.ConfigParser()
        config_path = f"{os.path.dirname(__file__)}/../.secret/config.ini"

        if not config.read(config_path):
            raise FileNotFoundError(os.path.abspath(config_path))

        self._conninfo = (
            f"dbname={config.get('Database', 'dbname')} "
            f"user={config.get('Database', 'user')} "
            f"password={config.get('Database', 'password')} "
            f"host={config.get('Database', 'host')} "
            f"port={config.getint('Database', 'port')}"
        )

        self._repos_path = config.get("Files", "repos_path")
        self._log_path = config.get("Files", "log_path")

        Path(self._log_path).mkdir(parents=True, exist_ok=True)

        self._task_queue: "asyncio.Queue[TaskInfo]" = asyncio.Queue()
        self._conn: psycopg.AsyncConnection | None = None
        self._work_conn: psycopg.AsyncConnection | None = None
        self._queue_task: asyncio.Task | None = None

    async def run(self) -> None:
        """Подключается к БД, подписывается на канал и обрабатывает очередь воркеров."""
        self._queue_task = asyncio.create_task(self._process_queue())

        # Отдельное соединение только для LISTEN/notifies - выполнение
        # запросов на этом же соединении зависает, пока notifies() ждёт уведомления.
        self._conn = await psycopg.AsyncConnection.connect(
            self._conninfo, autocommit=True
        )
        self._work_conn = await psycopg.AsyncConnection.connect(
            self._conninfo, autocommit=True
        )
        try:
            await self._conn.execute(f"LISTEN {NOTIFY_CHANNEL}")
            
            async for notify in self._conn.notifies():
                task_info = TaskInfo(**json.loads(notify.payload))

                if not task_info.type in SUPPORTED_TASK_TYPES:
                    continue

                async with self._work_conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE task SET status = 'queued' WHERE id = %s AND status = 'new'",
                        (task_info.id,),
                    )
                                        
                    if cur.rowcount != 1:
                        continue
                    
                    await cur.execute(
                        "SELECT data FROM task WHERE id = %s", (task_info.id,)
                    )
                    row = await cur.fetchone()
                    if row is not None:
                        task_info.data = row[0]

                print(f"QUEUED: id={task_info.id} type= {task_info.type}")
                await self._task_queue.put(task_info)
        finally:
            await self._conn.close()
            await self._work_conn.close()

    async def _process_queue(self) -> None:
        """Обрабатывает задачи по дной"""
        while True:
            task_info = await self._task_queue.get()
            try:
                await self._run_worker(task_info)
            except Exception:
                print(f"ERROR: id={task_info.id} type={task_info.type}")
                traceback.print_exc()
            self._task_queue.task_done()

    async def _run_worker(self, task_info: TaskInfo) -> None:
        """
        Запускает воркер в отдельном процессе.

        Используется subprocess.Popen (а не asyncio.create_subprocess_exec), т.к. на Windows
        asyncio-подпроцессы требуют ProactorEventLoop, а psycopg в async-режиме - наоборот,
        SelectorEventLoop. Ожидание завершения вынесено в отдельный поток, чтобы не блокировать loop.
        """
        async with self._work_conn.cursor() as cur:
            await cur.execute(
                "UPDATE task SET status = 'running' WHERE id = %s", (task_info.id,)
            )
        print(f"RUNNING: id={task_info.id} type= {task_info.type}")

        task_info.repos_path = self._repos_path

        try:
            with open(f"{self._log_path}/{task_info.id}.txt", "w") as out_file:
                process = subprocess.Popen(
                    [sys.executable, "-m", f"task_manager.tasks.{task_info.type}"],
                    cwd=PROJECT_ROOT,
                    stdin=subprocess.PIPE,
                    stdout=out_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                process.stdin.write(task_info.model_dump_json())
                process.stdin.close()
                returncode = await asyncio.to_thread(process.wait)
            status = "success" if returncode == 0 else "error"
        except Exception:
            traceback.print_exc()
            status = "error"

        print(f"{status.upper()}: id={task_info.id} type= {task_info.type}")

        async with self._work_conn.cursor() as cur:
            await cur.execute(
                "UPDATE task SET status = %s WHERE id = %s",
                (status, task_info.id),
            )


async def main() -> None:
    await TaskManager().run()


if __name__ == "__main__":
    asyncio.run(main())
