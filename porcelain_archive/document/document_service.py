from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import UploadFile
from psycopg.types.json import Jsonb

from pathlib import Path
import aiofiles

import base64
import json
import tempfile

from porcelain_archive.database import db
from porcelain_archive.user import role_at_least
from porcelain_archive.config import config

# Мок страницы документа: прозрачный PNG 1x1
_PLACEHOLDER_PAGE_IMAGE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

ALLOWED_PAGE_EXTENSIONS = {
    ".tiff",
    ".tif",
    ".jfif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
    ".raw",
    ".heic",
    ".heif",
}

BRANCH_STATUSES = {"in_work", "in_review", "in_accept", "accepted", "rejected"}

repos_root = str()
repos_branch_root = str()


class DocumentService:
    """
    Сервис для бизнес-логики, связанной с документами.
    Работает с таблицей document в БД.
    """

    @staticmethod
    def _row_to_document(row: Sequence[Any]) -> Dict[str, Any]:
        doc_id, name, meta, is_visible = row
        meta = meta or {}
        return {
            "id": doc_id,
            "name": name,
            "author": meta.get("author"),
            "created_at": meta.get("created_at"),
            "is_visible": bool(is_visible),
        }

    async def _can_see_hidden_documents(self, user_id: Optional[int]) -> bool:
        """Проверяет, видит ли пользователь скрытые (is_visible=0) документы (роль moderator+)."""
        if user_id is None:
            return False
        role = await db.get_user_role(user_id)
        return role_at_least(role, "moderator")

    async def get_document_count(self, user_id: Optional[int] = None) -> int:
        """
        Возвращает общее количество документов, доступных пользователю.
        Скрытые документы учитываются только для create/review.
        """
        if await self._can_see_hidden_documents(user_id):
            rows = await db.execute_read("SELECT COUNT(*) FROM document")
        else:
            rows = await db.execute_read("SELECT COUNT(*) FROM document WHERE is_visible = 1")
        return rows[0][0]

    async def get_documents_paginated(
        self, offset: int = 0, limit: int = 25, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка документов для пагинации. Скрытые документы
        видны только пользователю с правом create/review.

        :param offset: Смещение (сколько документов пропустить).
        :param limit: Количество документов для возврата.
        """
        if await self._can_see_hidden_documents(user_id):
            rows = await db.execute_read(
                "SELECT id, name, meta, is_visible FROM document ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset),
            )
        else:
            rows = await db.execute_read(
                "SELECT id, name, meta, is_visible FROM document WHERE is_visible = 1 ORDER BY id LIMIT %s OFFSET %s",
                (limit, offset),
            )
        return [self._row_to_document(row) for row in rows]

    async def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о документе по id.
        """
        rows = await db.execute_read(
            "SELECT id, name, meta, is_visible FROM document WHERE id = %s", (document_id,)
        )
        if not rows:
            return None

        return self._row_to_document(rows[0])

    async def set_document_visibility(self, document_id: int, is_visible: bool) -> bool:
        """
        Устанавливает видимость документа для обычных пользователей.
        """
        rows_affected = await db.execute_write(
            "UPDATE document SET is_visible = %s WHERE id = %s",
            (int(is_visible), document_id),
        )
        return rows_affected > 0

    async def create_document(self, name: str, author: str, user_id: int) -> int:
        """
        Создаёт новый документ и возвращает его id.

        :param name: Название документа.
        :param author: Автор документа (имя пользователя).
        :param user_id: Id пользователя, создающего документ (автор задачи).
        """
        async with db.transaction() as conn:
            cursor = await conn.execute(
                "INSERT INTO document (name, is_visible) VALUES (%s, 1) RETURNING id", (name,)
            )
            row = await cursor.fetchone()

            if row:
                await conn.execute(
                    "INSERT INTO branch (document_id, name, created_time) VALUES (%s, 'master', NOW()) RETURNING id",
                    (row[0],),
                )

                task_data = {"document_id": row[0]}
                await conn.execute(
                    "INSERT INTO task (type, author_id, data) VALUES ('create_repos', %s, %s) RETURNING id",
                    (user_id, Jsonb(task_data)),
                )

            return row[0]

    async def create_branch(self, user_id: int, document_id: int) -> int:
        """
        Создаёт новую ветку изменений для документа и возвращает её id.

        :param user_id: Автор ветки.
        :param document_id: Документ, к которому относится ветка.
        """
        async with db.transaction() as conn:
            cursor = await conn.execute(
                "SELECT id FROM document WHERE id = %s", (document_id,)
            )
            if await cursor.fetchone() is None:
                raise ValueError("Документ не найден")

            cursor = await conn.execute(
                "INSERT INTO branch (document_id, author_id, name, created_time) VALUES (%s, %s, %s, NOW()) RETURNING id",
                (document_id, user_id, f"branch"),
            )
            row = await cursor.fetchone()
            branch_id = row[0]
            branch_name = f"b-{branch_id}"

            await conn.execute(
                "UPDATE branch SET name = %s WHERE id = %s",
                (branch_name, branch_id),
            )

            if row:
                data = {
                    "document_id": document_id,
                    "branch_id": branch_id,
                    "branch_name": branch_name,
                }
                await conn.execute(
                    "INSERT INTO task (type, author_id, data) VALUES ('create_branch', %s, %s) RETURNING id",
                    (user_id, Jsonb(data)),
                )

            return branch_id

    async def is_document_available(
        self, user_id: Optional[int], document_id: int
    ) -> bool:
        """
        Проверяет, доступен ли документ для просмотра указанным пользователем.
        Видимые всем документы доступны без прав, скрытые - только create/review.
        """
        rows = await db.execute_read(
            "SELECT is_visible FROM document WHERE id = %s", (document_id,)
        )
        if not rows:
            return False

        if bool(rows[0][0]):
            return True
        if user_id is None:
            return False

        role = await db.get_user_role(user_id)
        return role_at_least(role, "moderator")

    async def is_edit_available(self, user_id: Optional[int], branch_id: int) -> bool:
        """
        Проверяет, доступна ли ветка редактирования указанному пользователю:
        автору ветки или пользователю с правом review.
        """
        if user_id is None:
            return False

        rows = await db.execute_read(
            "SELECT author_id FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows:
            return False

        if rows[0][0] == user_id:
            return True

        role = await db.get_user_role(user_id)
        return role_at_least(role, "moderator")

    async def is_branch_list_available(self, user_id: Optional[int]) -> bool:
        """
        Проверяет, доступен ли список наборов изменений указанному пользователю.
        Список виден только авторизованным пользователям.
        """
        return user_id is not None

    async def get_branch_count(self, user_id: Optional[int], sees_all: bool) -> int:
        """
        Возвращает количество наборов изменений, видимых пользователю.
        sees_all (роль moderator+) видит все, иначе - только свои.
        """
        if sees_all:
            rows = await db.execute_read(
                "SELECT COUNT(*) FROM branch WHERE name != 'master'"
            )
        else:
            rows = await db.execute_read(
                "SELECT COUNT(*) FROM branch WHERE name != 'master' AND author_id = %s",
                (user_id,),
            )
        return rows[0][0]

    async def get_branches_paginated(
        self, user_id: Optional[int], sees_all: bool, offset: int = 0, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Возвращает срез списка наборов изменений, видимых пользователю.
        sees_all (роль moderator+) видит все, иначе - только свои.
        """
        query = """
            SELECT b.id, b.document_id, d.name, b.author_id, a.display_name, b.created_time, b.last_change_time, b.status
            FROM branch b
            JOIN document d ON d.id = b.document_id
            LEFT JOIN member a ON a.id = b.author_id
            WHERE b.name != 'master'
        """
        params: List[Any] = []
        if not sees_all:
            query += " AND b.author_id = %s"
            params.append(user_id)
        query += " ORDER BY b.id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        rows = await db.execute_read(query, tuple(params))
        return [
            {
                "id": row[0],
                "document_id": row[1],
                "document_name": row[2],
                "author_id": row[3],
                "author_name": row[4],
                "created_at": row[5],
                "last_change_at": row[6],
                "status": row[7],
            }
            for row in rows
        ]

    async def get_branch_info(self, branch_id: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает информацию о ветке: id, документ, название документа, имя ветки, автор, статус.
        """
        rows = await db.execute_read(
            """
            SELECT b.id, b.document_id, d.name, b.name, b.author_id, b.status, b.initial_commit, b.last_commit
            FROM branch b
            JOIN document d ON d.id = b.document_id
            WHERE b.id = %s
            """,
            (branch_id,),
        )
        if not rows:
            return None

        branch_id_, document_id, document_name, branch_name, author_id, branch_status, initial_commit, last_commit = rows[0]
        return {
            "id": branch_id_,
            "document_id": document_id,
            "document_name": document_name,
            "name": branch_name,
            "author_id": author_id,
            "status": branch_status,
            "initial_commit": initial_commit,
            "last_commit": last_commit,
        }

    async def is_branch_author(self, user_id: Optional[int], branch_id: int) -> bool:
        """Проверяет, является ли пользователь автором (создателем) ветки."""
        if user_id is None:
            return False

        rows = await db.execute_read(
            "SELECT author_id FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows:
            return False

        return rows[0][0] == user_id

    async def submit_branch_for_review(self, branch_id: int) -> None:
        """Переводит набор изменений из 'в работе' в 'на проверке'."""
        rows_affected = await db.execute_write(
            "UPDATE branch SET status = 'in_review' WHERE id = %s AND status = 'in_work'",
            (branch_id,),
        )
        if rows_affected == 0:
            raise ValueError("Набор изменений не в статусе 'в работе'")

    async def return_branch_to_work(self, branch_id: int) -> None:
        """Переводит набор изменений из 'на проверке' обратно в 'в работе'."""
        rows_affected = await db.execute_write(
            "UPDATE branch SET status = 'in_work' WHERE id = %s AND status = 'in_review'",
            (branch_id,),
        )
        if rows_affected == 0:
            raise ValueError("Набор изменений не в статусе 'на проверке'")

    async def set_branch_status(self, branch_id: int, new_status: str, user_id: int) -> None:
        """
        Устанавливает статус набора изменений напрямую (для moderator+).
        'accepted' выставляется только автоматически по результату задачи
        merge_branch. 'in_accept' запускает слияние ветки в master вместо
        обычного изменения статуса.
        """
        if new_status not in BRANCH_STATUSES:
            raise ValueError(f"Неизвестный статус: '{new_status}'")
        if new_status == "accepted":
            raise ValueError("Статус 'Принято' выставляется автоматически при успешном завершении правок")

        if new_status == "in_accept":
            await self._start_merge(branch_id, user_id)
            return

        rows_affected = await db.execute_write(
            "UPDATE branch SET status = %s WHERE id = %s",
            (new_status, branch_id),
        )
        if rows_affected == 0:
            raise ValueError("Ветка не найдена")

    async def _start_merge(self, branch_id: int, user_id: int) -> None:
        """
        Переводит набор изменений в 'Завершение правок' и ставит в очередь
        его слияние в master. Возможно только для набора изменений в статусе
        'Проверяется'.
        """
        rows = await db.execute_read(
            "SELECT document_id, name, status FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows:
            raise ValueError("Ветка не найдена")

        document_id, branch_name, branch_status = rows[0]
        if branch_name == "master":
            raise ValueError("master нельзя слить саму в себя")
        if branch_status != "in_review":
            raise ValueError("Завершить правки можно только для набора изменений в статусе 'Проверяется'")

        async with db.transaction() as conn:
            await conn.execute(
                "UPDATE branch SET status = 'in_accept' WHERE id = %s", (branch_id,)
            )

            data = {
                "branch_id": branch_id,
                "branch_name": branch_name,
                "document_id": document_id,
            }
            await conn.execute(
                "INSERT INTO task (type, author_id, data) VALUES ('merge_branch', %s, %s) RETURNING id",
                (user_id, Jsonb(data)),
            )

    async def is_branch_viewable(self, user_id: Optional[int], branch_id: int) -> bool:
        """
        Проверяет, доступен ли просмотр страниц ветки: как is_edit_available,
        плюс master-ветка доступна всем, кому доступен сам документ.
        """
        if await self.is_edit_available(user_id, branch_id):
            return True

        rows = await db.execute_read(
            "SELECT document_id, name FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows:
            return False

        document_id, branch_name = rows[0]
        if branch_name != "master":
            return False

        return await self.is_document_available(user_id, document_id)

    async def add_pages(
        self, branch_id: int, files: List[UploadFile], position: int, user_id: int
    ) -> Dict[str, Any]:
        """
        Добавляет страницы (файлы изображений) в ветку изменений.

        :param branch_id: Ветка, в которую добавляются страницы.
        :param files: Загруженные файлы изображений.
        :param position: Номер страницы, после которой вставлять (0 - в начало).
        :param user_id: Пользователь, запустивший задачу.
        """
        
        page_count = await self.get_branch_page_count(branch_id)
        if not (0 <= int(position) <= page_count):
            raise ValueError(f"position должен быть в диапазоне от 0 до {page_count}")

        for file in files:
            extension = Path(file.filename).suffix.lower()
            if extension not in ALLOWED_PAGE_EXTENSIONS:
                raise ValueError(f"Недопустимый формат файла: '{extension}'")

        tmpdir = tempfile.mkdtemp()
        print(f"Временная папка: {tmpdir}")

        page_num = position
        for file in files:
            page_num += 1
            extension = Path(file.filename).suffix.lower()
            dest_file_path = f"{tmpdir}/{page_num}{extension}"
            async with aiofiles.open(dest_file_path, "wb") as out_file:
                while chunk := await file.read(1024 * 1024):
                    await out_file.write(chunk)

        async with db.transaction() as conn:
            data = {
                "branch_id": branch_id,
                "branch_name": "b-" + str(branch_id),
                "position": position,
                "tmpdir": tmpdir,
            }
            await conn.execute(
                "INSERT INTO task (type, author_id, data) VALUES ('insert_files', %s, %s) RETURNING id",
                (user_id, Jsonb(data)),
            )

        return {}

    async def remove_pages(self, branch_id: int, start: int, end: int, user_id: int) -> Dict[str, Any]:
        """
        Удаляет диапазон страниц [start, end] (включительно) из ветки изменений.

        :param branch_id: Ветка, из которой удаляются страницы.
        :param start: Первая удаляемая страница.
        :param end: Последняя удаляемая страница.
        :param user_id: Пользователь, запустивший задачу.
        """
        page_count = await self.get_branch_page_count(branch_id)
        if not (1 <= int(start) <= int(end) <= page_count):
            raise ValueError(f"Диапазон должен быть в пределах от 1 до {page_count}")

        async with db.transaction() as conn:
            data = {
                "branch_id": branch_id,
                "branch_name": "b-" + str(branch_id),
                "position": start,
                "file_remove_count": end - start + 1,
            }
            await conn.execute(
                "INSERT INTO task (type, author_id, data) VALUES ('remove_files', %s, %s) RETURNING id",
                (user_id, Jsonb(data)),
            )

        return {}

    async def set_text(self, branch_id: int, file: UploadFile, position: int, user_id: int) -> Dict[str, Any]:
        """
        Загружает PDF и ставит в очередь применение его текста к страницам
        ветки, начиная с position.

        :param branch_id: Ветка, к которой применяется текст.
        :param file: Загруженный PDF-файл.
        :param position: Номер страницы, с которой начинается применение текста.
        :param user_id: Пользователь, запустивший задачу.
        """
        page_count = await self.get_branch_page_count(branch_id)
        if not (1 <= int(position) <= page_count):
            raise ValueError(f"position должен быть в диапазоне от 1 до {page_count}")

        extension = Path(file.filename).suffix.lower()
        if extension != ".pdf":
            raise ValueError(f"Недопустимый формат файла: '{extension}', ожидается .pdf")

        tmpdir = tempfile.mkdtemp()
        print(f"Временная папка: {tmpdir}")

        pdf_path = f"{tmpdir}/{file.filename}"
        async with aiofiles.open(pdf_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):
                await out_file.write(chunk)

        async with db.transaction() as conn:
            data = {
                "branch_id": branch_id,
                "branch_name": "b-" + str(branch_id),
                "position": position,
                "pdf_path": pdf_path,
            }
            await conn.execute(
                "INSERT INTO task (type, author_id, data) VALUES ('set_text', %s, %s) RETURNING id",
                (user_id, Jsonb(data)),
            )

        return {}

    async def reset_text(self, branch_id: int, start: int, end: int, user_id: int) -> Dict[str, Any]:
        """
        Ставит в очередь удаление текста со страниц [start, end] (включительно).

        :param branch_id: Ветка, из которой удаляется текст.
        :param start: Первая страница диапазона.
        :param end: Последняя страница диапазона.
        :param user_id: Пользователь, запустивший задачу.
        """
        page_count = await self.get_branch_page_count(branch_id)
        if not (1 <= int(start) <= int(end) <= page_count):
            raise ValueError(f"Диапазон должен быть в пределах от 1 до {page_count}")

        async with db.transaction() as conn:
            data = {
                "branch_id": branch_id,
                "branch_name": "b-" + str(branch_id),
                "start": start,
                "end": end,
            }
            await conn.execute(
                "INSERT INTO task (type, author_id, data) VALUES ('reset_text', %s, %s) RETURNING id",
                (user_id, Jsonb(data)),
            )

        return {}

    async def get_master_branch_id(self, document_id: int) -> Optional[int]:
        """
        Возвращает id основной (master) ветки документа.
        """
        rows = await db.execute_read(
            "SELECT id FROM branch WHERE document_id = %s AND name = 'master'",
            (document_id,),
        )
        if not rows:
            return None

        return rows[0][0]

    async def get_branch_page_count(self, branch_id: int) -> int:
        """
        Возвращает количество страниц в ветке.
        """
        rows = await db.execute_read(
            "SELECT meta->>'page_count' FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows or rows[0][0] is None:
            return 0

        return int(rows[0][0])

    async def get_branch_last_commit(self, branch_id: int) -> Optional[str]:
        """
        Возвращает коммит последнего обновления кеша страниц ветки.
        """
        rows = await db.execute_read(
            "SELECT last_commit FROM branch WHERE id = %s", (branch_id,)
        )
        if not rows:
            return None

        return rows[0][0]

    async def get_pages_hash(self, commit: Optional[str]) -> List[Dict[str, Optional[str]]]:
        """
        Возвращает image_hash и text_hash всех страниц указанного коммита, упорядоченных по номеру страницы.
        """
        if commit is None:
            return []

        rows = await db.execute_read(
            "SELECT image_hash, text_hash FROM page WHERE commit = %s ORDER BY pos",
            (commit,),
        )
        return [{"image_hash": row[0], "text_hash": row[1]} for row in rows]

    def get_allowed_page_extensions(self) -> List[str]:
        """
        Возвращает список расширений файлов, допустимых для страниц документа.
        """
        return sorted(ALLOWED_PAGE_EXTENSIONS)

    async def _get_page_image_hash(self, commit: Optional[str], page_index: int) -> Optional[str]:
        """
        Возвращает image_hash страницы коммита по её номеру.
        """
        if commit is None:
            return None

        rows = await db.execute_read(
            "SELECT image_hash FROM page WHERE commit = %s AND pos = %s",
            (commit, page_index),
        )
        if not rows or rows[0][0] is None:
            return None

        return rows[0][0]

    async def get_page_image(self, commit: Optional[str], page_index: int) -> Tuple[bytes, str]:
        """
        Возвращает изображение страницы коммита.
        """
        image_hash = await self._get_page_image_hash(commit, page_index)
        if image_hash is None:
            return _PLACEHOLDER_PAGE_IMAGE, "image/png"

        image_path = Path(config.files.cache_path) / "web" / f"{image_hash}.jpg"
        if not image_path.exists():
            return _PLACEHOLDER_PAGE_IMAGE, "image/png"

        return image_path.read_bytes(), "image/jpeg"

    async def get_page_image_preview(self, commit: Optional[str], page_index: int) -> Tuple[bytes, str]:
        """
        Возвращает превью изображения страницы коммита.
        """
        image_hash = await self._get_page_image_hash(commit, page_index)
        if image_hash is None:
            return _PLACEHOLDER_PAGE_IMAGE, "image/png"

        image_path = Path(config.files.cache_path) / "preview" / f"{image_hash}.jpg"
        if not image_path.exists():
            return _PLACEHOLDER_PAGE_IMAGE, "image/png"

        return image_path.read_bytes(), "image/jpeg"

    async def _get_page_text_hash(self, commit: Optional[str], page_index: int) -> Optional[str]:
        """
        Возвращает text_hash страницы коммита по её номеру.
        """
        if commit is None:
            return None

        rows = await db.execute_read(
            "SELECT text_hash FROM page WHERE commit = %s AND pos = %s",
            (commit, page_index),
        )
        if not rows or rows[0][0] is None:
            return None

        return rows[0][0]

    async def get_page_text(self, commit: Optional[str], page_index: int) -> Optional[Dict[str, Any]]:
        """
        Возвращает текст страницы коммита (блоки/спаны, извлечённые из PDF), если он задан.
        """
        text_hash = await self._get_page_text_hash(commit, page_index)
        if text_hash is None:
            return None

        text_path = Path(config.files.cache_path) / "json" / f"{text_hash}.json"
        if not text_path.exists():
            return None

        try:
            return json.loads(text_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            # Повреждённый или недописанный файл кеша (например, из-за упавшей
            # задачи set_text) - считаем, что текст не задан, а не 500-м.
            return None
