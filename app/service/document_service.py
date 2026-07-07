from datetime import date
from typing import Any, Dict, List, Sequence

from psycopg.types.json import Jsonb

from app.database import db


class DocumentService:
    """
    Сервис для бизнес-логики, связанной с документами.
    Работает с таблицей document в БД.
    """

    @staticmethod
    def _row_to_document(row: Sequence[Any]) -> Dict[str, Any]:
        doc_id, name, meta = row
        meta = meta or {}
        return {
            "id": doc_id,
            "name": name,
            "author": meta.get("author"),
            "created_at": meta.get("created_at"),
        }

    async def get_document_count(self) -> int:
        """
        Возвращает общее количество документов.
        """
        rows = await db.execute_read("SELECT COUNT(*) FROM document")
        return rows[0][0]

    async def get_documents_paginated(self, offset: int = 0, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка документов для пагинации.

        :param offset: Смещение (сколько документов пропустить).
        :param limit: Количество документов для возврата.
        """
        rows = await db.execute_read(
            "SELECT id, name, meta FROM document ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        return [self._row_to_document(row) for row in rows]

    async def create_document(self, name: str, author: str) -> int:
        """
        Создаёт новый документ и возвращает его id.

        :param name: Название документа.
        :param author: Автор документа (имя пользователя).
        """
        meta = {"author": author, "created_at": date.today().isoformat()}
        async with db.transaction() as conn:
            cursor = await conn.execute(
                "INSERT INTO document (name, meta) VALUES (%s, %s) RETURNING id",
                (name, Jsonb(meta))
            )
            row = await cursor.fetchone()
            
            if row:
                await conn.execute(
                    "INSERT INTO task (type, data) VALUES ('create_repos', %s) RETURNING id",
                    (Jsonb(meta), )
                )   
            
            return row[0]
