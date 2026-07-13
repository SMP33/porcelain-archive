import asyncio
import os
from typing import Any, Dict, List, Optional, Sequence

from porcelain_archive.database import db
from porcelain_archive.config import config
from porcelain_archive import logging_setup


class TaskService:
    """
    Сервис для бизнес-логики, связанной с задачами task_manager.
    Работает с таблицей task в БД.
    """

    @staticmethod
    def _row_to_task(row: Sequence[Any]) -> Dict[str, Any]:
        task_id, type_, status, data, author_id, author_display_name = row
        return {
            "id": task_id,
            "type": type_,
            "status": status,
            "data": data or {},
            "author_id": author_id,
            "author_display_name": author_display_name,
        }

    async def get_task_count(self) -> int:
        """
        Возвращает общее количество задач.
        """
        rows = await db.execute_read("SELECT COUNT(*) FROM task")
        return rows[0][0]

    async def get_tasks_paginated(self, offset: int = 0, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка задач для пагинации, отсортированный от новых к старым.

        :param offset: Смещение (сколько задач пропустить).
        :param limit: Количество задач для возврата.
        """
        rows = await db.execute_read(
            """
            SELECT t.id, t.type, t.status, t.data, t.author_id, a.display_name
            FROM task t
            LEFT JOIN member a ON a.id = t.author_id
            ORDER BY t.id DESC LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return [self._row_to_task(row) for row in rows]

    async def get_tasks_by_branch_id(self, branch_id: int) -> List[Dict[str, Any]]:
        """
        Возвращает задачи, относящиеся к указанной ветке (data->>'branch_id'), от новых к старым.
        """
        rows = await db.execute_read(
            """
            SELECT t.id, t.type, t.status, t.data, t.author_id, a.display_name
            FROM task t
            LEFT JOIN member a ON a.id = t.author_id
            WHERE t.data->>'branch_id' = %s ORDER BY t.id DESC
            """,
            (str(branch_id),),
        )
        return [self._row_to_task(row) for row in rows]

    async def is_task_list_available(self, user_id: Optional[int]) -> bool:
        """
        Проверяет, доступен ли список задач указанному пользователю.
        Список задач виден только авторизованным пользователям.
        """
        return user_id is not None

    async def get_task_log(self, task_id: int) -> str:
        """
        Возвращает содержимое лог-файла задачи.
        """
        log_file_path = os.path.join(config.files.log_path, f"{task_id}.txt")
        print(f"LOG: {log_file_path}")
        if not os.path.exists(log_file_path):
            return ""

        with open(log_file_path, "r", encoding="utf-8") as log_file:
            return log_file.read()

    async def get_server_log(self) -> str:
        """
        Возвращает содержимое файла лога текущего запуска сервера.
        """
        log_file_path = logging_setup.get_current_log_file()
        if not log_file_path or not os.path.exists(log_file_path):
            return ""

        def _read() -> str:
            with open(log_file_path, "r", encoding="utf-8") as log_file:
                return log_file.read()

        return await asyncio.to_thread(_read)
