import re
from typing import Any, Dict, List, Optional

from porcelain_archive.database import db

TAG_PATTERN = re.compile(r"^[a-z_]+$")
PROPERTY_TYPES = {"string", "bool", "combobox", "multicheckbox"}


class PropertyService:
    async def get_properties(self) -> List[Dict[str, Any]]:
        """Возвращает все указатели (property) в порядке view_order."""
        rows = await db.execute_read(
            """
            SELECT p.id, p.tag, p.title, p.description, p.type, p.is_editable,
                   p.is_usable, p.is_visible, p.is_system, p.view_order,
                   EXISTS (
                       SELECT 1 FROM document_property dp
                       WHERE dp.tag = p.tag AND dp.document_id IS NOT NULL
                   ) AS in_use
            FROM property p
            ORDER BY p.view_order, p.id
            """
        )
        return [self._row_to_property(row) for row in rows]

    def _row_to_property(self, row) -> Dict[str, Any]:
        id_, tag, title, description, type_, is_editable, is_usable, is_visible, is_system, view_order, in_use = row
        return {
            "id": id_,
            "tag": tag,
            "title": title,
            "description": description,
            "type": type_,
            "is_editable": bool(is_editable),
            "is_usable": bool(is_usable),
            "is_visible": bool(is_visible),
            "is_system": bool(is_system),
            "view_order": view_order,
            "in_use": bool(in_use),
        }

    async def create_property(
        self,
        tag: str,
        title: str,
        description: Optional[str],
        type: str,
        is_editable: bool,
        is_usable: bool,
        is_visible: bool,
    ) -> int:
        """Создаёт новый указатель и возвращает его id."""
        if not TAG_PATTERN.match(tag):
            raise ValueError("Указатель должен состоять только из маленьких латинских букв и символа '_'")
        if type not in PROPERTY_TYPES:
            raise ValueError(f"Неизвестный тип указателя: '{type}'")

        existing = await db.execute_read(
            "SELECT 1 FROM property WHERE tag = %s OR title = %s", (tag, title)
        )
        if existing:
            raise ValueError("Указатель с таким tag или названием уже существует")

        async with db.transaction() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO property (tag, title, description, type, is_editable, is_usable, is_visible)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (tag, title, description, type, int(is_editable), int(is_usable), int(is_visible)),
            )
            row = await cursor.fetchone()
            return row[0]

    async def update_property_title(self, property_id: int, title: str) -> bool:
        """Изменяет отображаемое имя указателя (tag и type после создания не меняются)."""
        rows = await db.execute_read("SELECT is_editable FROM property WHERE id = %s", (property_id,))
        if not rows:
            return False
        if not rows[0][0]:
            raise ValueError("Название этого указателя изменить нельзя")

        existing = await db.execute_read(
            "SELECT 1 FROM property WHERE title = %s AND id != %s", (title, property_id)
        )
        if existing:
            raise ValueError(f"Указатель с названием '{title}' уже существует")

        rows_affected = await db.execute_write(
            "UPDATE property SET title = %s WHERE id = %s", (title, property_id)
        )
        return rows_affected > 0

    async def update_property_description(self, property_id: int, description: Optional[str]) -> bool:
        """Изменяет описание указателя."""
        rows = await db.execute_read("SELECT is_editable FROM property WHERE id = %s", (property_id,))
        if not rows:
            return False
        if not rows[0][0]:
            raise ValueError("Описание этого указателя изменить нельзя")

        rows_affected = await db.execute_write(
            "UPDATE property SET description = %s WHERE id = %s", (description, property_id)
        )
        return rows_affected > 0

    async def update_property_flags(
        self, property_id: int, is_editable: bool, is_usable: bool, is_visible: bool
    ) -> bool:
        """Изменяет флаги указателя."""
        rows_affected = await db.execute_write(
            "UPDATE property SET is_editable = %s, is_usable = %s, is_visible = %s WHERE id = %s",
            (int(is_editable), int(is_usable), int(is_visible), property_id),
        )
        return rows_affected > 0

    async def reorder_properties(self, ordered_ids: List[int]) -> None:
        """Проставляет view_order по позиции id в переданном списке."""
        async with db.transaction() as conn:
            for position, property_id in enumerate(ordered_ids):
                await conn.execute(
                    "UPDATE property SET view_order = %s WHERE id = %s", (position, property_id)
                )

    async def delete_property(self, property_id: int) -> bool:
        """
        Удаляет указатель. Нельзя удалить системный указатель (is_system) или
        указатель, у которого хоть одно значение уже проставлено документу.
        """
        rows = await db.execute_read("SELECT tag, is_system FROM property WHERE id = %s", (property_id,))
        if not rows:
            return False
        tag, is_system = rows[0]
        if is_system:
            raise ValueError("Системный указатель нельзя удалить")

        in_use = await db.execute_read(
            "SELECT 1 FROM document_property WHERE tag = %s AND document_id IS NOT NULL", (tag,)
        )
        if in_use:
            raise ValueError("Указатель используется в документах и не может быть удалён")

        rows_affected = await db.execute_write("DELETE FROM property WHERE id = %s", (property_id,))
        return rows_affected > 0

    async def _get_editable_tag(self, property_id: int) -> str:
        """Возвращает tag указателя, если разрешено редактировать список его значений."""
        rows = await db.execute_read(
            "SELECT tag, is_editable FROM property WHERE id = %s", (property_id,)
        )
        if not rows:
            raise ValueError("Указатель не найден")
        tag, is_editable = rows[0]
        if not is_editable:
            raise ValueError("Список значений этого указателя нельзя редактировать")
        return tag

    async def get_property_enum_values(self, property_id: int) -> List[Dict[str, Any]]:
        """Возвращает допустимые значения указателя (пул для combobox/multicheckbox)."""
        rows = await db.execute_read(
            """
            SELECT dp.value FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            WHERE p.id = %s AND dp.document_id IS NULL
            ORDER BY dp.value
            """,
            (property_id,),
        )
        return [{"value": row[0]} for row in rows]

    def _validate_enum_value(self, value: str) -> None:
        """Проверяет значение указателя: не пустое и без пробелов по краям."""
        if not value:
            raise ValueError("Значение не может быть пустым")
        if value != value.strip():
            raise ValueError("Значение не должно начинаться или заканчиваться пробельным символом")

    async def create_property_enum_value(self, property_id: int, value: str) -> None:
        """Добавляет допустимое значение указателя."""
        self._validate_enum_value(value)
        tag = await self._get_editable_tag(property_id)

        existing = await db.execute_read(
            "SELECT 1 FROM document_property WHERE tag = %s AND document_id IS NULL AND value = %s",
            (tag, value),
        )
        if existing:
            raise ValueError(f"Значение '{value}' уже существует для этого указателя")

        await db.execute_write(
            "INSERT INTO document_property (document_id, tag, value) VALUES (NULL, %s, %s)",
            (tag, value),
        )

    async def update_property_enum_value(self, property_id: int, old_value: str, new_value: str) -> bool:
        """Переименовывает допустимое значение указателя всюду, где оно используется."""
        self._validate_enum_value(new_value)
        tag = await self._get_editable_tag(property_id)
        if old_value == new_value:
            return True

        existing = await db.execute_read(
            "SELECT 1 FROM document_property WHERE tag = %s AND document_id IS NULL AND value = %s",
            (tag, new_value),
        )
        if existing:
            raise ValueError(f"Значение '{new_value}' уже существует для этого указателя")

        rows_affected = await db.execute_write(
            "UPDATE document_property SET value = %s WHERE tag = %s AND value = %s",
            (new_value, tag, old_value),
        )
        return rows_affected > 0

    async def delete_property_enum_value(self, property_id: int, value: str) -> bool:
        """
        Удаляет допустимое значение указателя. Нельзя удалить значение,
        которое уже проставлено хотя бы одному документу.
        """
        tag = await self._get_editable_tag(property_id)

        in_use = await db.execute_read(
            "SELECT 1 FROM document_property WHERE tag = %s AND value = %s AND document_id IS NOT NULL",
            (tag, value),
        )
        if in_use:
            raise ValueError("Значение используется в документах и не может быть удалено")

        rows_affected = await db.execute_write(
            "DELETE FROM document_property WHERE tag = %s AND value = %s AND document_id IS NULL",
            (tag, value),
        )
        return rows_affected > 0

    async def validate_value(self, tag: str, value: str) -> bool:
        """
        Проверяет, допустимо ли значение для указателя с данным tag: для bool -
        только 'true'/'false', для combobox/multicheckbox - только значение,
        уже существующее в пуле допустимых (document_property, document_id = NULL),
        для string - любое значение.
        """
        rows = await db.execute_read("SELECT type FROM property WHERE tag = %s", (tag,))
        if not rows:
            raise ValueError("Указатель не найден")
        type_ = rows[0][0]

        if type_ == "bool":
            return value in ("true", "false")

        if type_ in ("combobox", "multicheckbox"):
            existing = await db.execute_read(
                "SELECT 1 FROM document_property WHERE tag = %s AND value = %s AND document_id IS NULL",
                (tag, value),
            )
            return bool(existing)

        return True

    async def get_property_values(self, property_id: int) -> List[str]:
        """Возвращает все различные значения, когда-либо использованные для указателя."""
        rows = await db.execute_read(
            """
            SELECT DISTINCT dp.value FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            WHERE p.id = %s
            ORDER BY dp.value
            """,
            (property_id,),
        )
        return [row[0] for row in rows]

    async def get_property_value_counts(self, property_id: int, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Возвращает значения указателя, проставленные документам, и количество
        документов для каждого значения. query - фильтр по подстроке (ILIKE).
        """
        rows = await db.execute_read(
            """
            SELECT dp.value, COUNT(DISTINCT dp.document_id) AS count
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            WHERE p.id = %s AND dp.document_id IS NOT NULL
              AND (%s::text IS NULL OR dp.value ILIKE '%%' || %s || '%%')
            GROUP BY dp.value
            ORDER BY dp.value
            """,
            (property_id, query, query),
        )
        return [{"value": row[0], "count": row[1]} for row in rows]

    async def get_documents_by_property_value(self, property_id: int, value: str) -> List[Dict[str, Any]]:
        """Возвращает документы, у которых указателю проставлено данное значение."""
        rows = await db.execute_read(
            """
            SELECT d.id, d.name
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            JOIN document d ON d.id = dp.document_id
            WHERE p.id = %s AND dp.value = %s
            ORDER BY d.name
            """,
            (property_id, value),
        )
        return [{"id": row[0], "name": row[1]} for row in rows]

    async def get_property_translations(self, property_id: int) -> List[Dict[str, Any]]:
        """Возвращает переводы значений указателя (property_translate)."""
        rows = await db.execute_read(
            """
            SELECT pt.value, pt.translated
            FROM property_translate pt
            JOIN property p ON p.tag = pt.tag
            WHERE p.id = %s
            ORDER BY pt.value
            """,
            (property_id,),
        )
        return [{"value": row[0], "translated": row[1]} for row in rows]

    async def _get_translatable_tag(self, property_id: int) -> str:
        """Возвращает tag указателя, если для его типа выполняется перевод (не string) и разрешено редактирование."""
        rows = await db.execute_read("SELECT tag, type, is_editable FROM property WHERE id = %s", (property_id,))
        if not rows:
            raise ValueError("Указатель не найден")
        tag, type_, is_editable = rows[0]
        if type_ == "string":
            raise ValueError("Для указателей типа 'строка' перевод не выполняется")
        if not is_editable:
            raise ValueError("Перевод этого указателя изменить нельзя")
        return tag

    async def set_property_translation(self, property_id: int, value: str, translated: str) -> None:
        """Добавляет или изменяет перевод значения указателя."""
        tag = await self._get_translatable_tag(property_id)
        await db.execute_write(
            """
            INSERT INTO property_translate (tag, value, translated) VALUES (%s, %s, %s)
            ON CONFLICT (tag, value) DO UPDATE SET translated = EXCLUDED.translated
            """,
            (tag, value, translated),
        )

    async def delete_property_translation(self, property_id: int, value: str) -> bool:
        """Удаляет перевод значения указателя (значение снова отображается как есть)."""
        tag = await self._get_translatable_tag(property_id)
        rows_affected = await db.execute_write(
            "DELETE FROM property_translate WHERE tag = %s AND value = %s", (tag, value)
        )
        return rows_affected > 0
