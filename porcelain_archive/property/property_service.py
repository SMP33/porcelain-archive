import re
from typing import Any, Dict, List, Optional

from porcelain_archive.database import db

TAG_PATTERN = re.compile(r"^[a-z_]+$")


class PropertyService:
    async def get_properties(self) -> List[Dict[str, Any]]:
        """Возвращает все указатели (property), в порядке view_order."""
        rows = await db.execute_read(
            """
            SELECT p.id, p.tag, p.title, p.description, p.is_list, p.is_editable,
                   p.is_visible, p.is_system, p.view_order,
                   EXISTS (
                       SELECT 1 FROM document_property dp
                       JOIN property_enum pe ON pe.id = dp.property_enum_id
                       WHERE pe.property_id = p.id
                   ) AS in_use
            FROM property p
            ORDER BY p.view_order, p.id
            """
        )
        return [self._row_to_property(row) for row in rows]

    def _row_to_property(self, row) -> Dict[str, Any]:
        id_, tag, title, description, is_list, is_editable, is_visible, is_system, view_order, in_use = row
        return {
            "id": id_,
            "tag": tag,
            "title": title,
            "description": description,
            "is_list": bool(is_list),
            "is_editable": bool(is_editable),
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
        is_list: bool,
        is_editable: bool,
        is_visible: bool,
    ) -> int:
        """Создаёт новый указатель и возвращает его id."""
        if not TAG_PATTERN.match(tag):
            raise ValueError("Указатель должен состоять только из маленьких латинских букв и символа '_'")

        existing = await db.execute_read(
            "SELECT 1 FROM property WHERE tag = %s OR title = %s", (tag, title)
        )
        if existing:
            raise ValueError("Указатель с таким tag или названием уже существует")

        async with db.transaction() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO property (tag, title, description, is_list, is_editable, is_visible)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (tag, title, description, int(is_list), int(is_editable), int(is_visible)),
            )
            row = await cursor.fetchone()
            return row[0]

    async def update_property_title(self, property_id: int, title: str) -> bool:
        """Изменяет отображаемое имя указателя (tag после создания не меняется)."""
        existing = await db.execute_read(
            "SELECT 1 FROM property WHERE title = %s AND id != %s", (title, property_id)
        )
        if existing:
            raise ValueError(f"Указатель с названием '{title}' уже существует")

        rows_affected = await db.execute_write(
            "UPDATE property SET title = %s WHERE id = %s", (title, property_id)
        )
        return rows_affected > 0

    async def update_property_flags(
        self, property_id: int, is_list: bool, is_editable: bool, is_visible: bool
    ) -> bool:
        """Изменяет флаги указателя. Недоступно для системных указателей (is_system)."""
        rows = await db.execute_read("SELECT is_system FROM property WHERE id = %s", (property_id,))
        if not rows:
            raise ValueError("Указатель не найден")
        if bool(rows[0][0]):
            raise ValueError("Флаги системного указателя изменить нельзя")

        rows_affected = await db.execute_write(
            "UPDATE property SET is_list = %s, is_editable = %s, is_visible = %s WHERE id = %s",
            (int(is_list), int(is_editable), int(is_visible), property_id),
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
        Удаляет указатель. Нельзя удалить указатель, у которого хоть одно
        значение уже используется в document_property.
        """
        in_use = await db.execute_read(
            """
            SELECT 1 FROM document_property dp
            JOIN property_enum pe ON pe.id = dp.property_enum_id
            WHERE pe.property_id = %s
            """,
            (property_id,),
        )
        if in_use:
            raise ValueError("Указатель используется в документах и не может быть удалён")

        rows_affected = await db.execute_write("DELETE FROM property WHERE id = %s", (property_id,))
        return rows_affected > 0

    async def get_property_enum_values(self, property_id: int) -> List[Dict[str, Any]]:
        """Возвращает допустимые значения указателя."""
        rows = await db.execute_read(
            "SELECT id, value FROM property_enum WHERE property_id = %s ORDER BY value", (property_id,)
        )
        return [{"id": row[0], "value": row[1]} for row in rows]

    async def create_property_enum_value(self, property_id: int, value: str) -> int:
        """Добавляет допустимое значение указателя и возвращает его id."""
        property_rows = await db.execute_read("SELECT 1 FROM property WHERE id = %s", (property_id,))
        if not property_rows:
            raise ValueError("Указатель не найден")

        existing = await db.execute_read(
            "SELECT 1 FROM property_enum WHERE property_id = %s AND value = %s", (property_id, value)
        )
        if existing:
            raise ValueError(f"Значение '{value}' уже существует для этого указателя")

        async with db.transaction() as conn:
            cursor = await conn.execute(
                "INSERT INTO property_enum (property_id, value) VALUES (%s, %s) RETURNING id",
                (property_id, value),
            )
            row = await cursor.fetchone()
            return row[0]

    async def update_property_enum_value(self, enum_id: int, new_value: str) -> bool:
        """Переименовывает допустимое значение указателя по его id."""
        rows = await db.execute_read("SELECT property_id, value FROM property_enum WHERE id = %s", (enum_id,))
        if not rows:
            raise ValueError("Значение не найдено")
        property_id, old_value = rows[0]
        if old_value == new_value:
            return True

        existing = await db.execute_read(
            "SELECT 1 FROM property_enum WHERE property_id = %s AND value = %s AND id != %s",
            (property_id, new_value, enum_id),
        )
        if existing:
            raise ValueError(f"Значение '{new_value}' уже существует для этого указателя")

        await db.execute_write("UPDATE property_enum SET value = %s WHERE id = %s", (new_value, enum_id))
        return True

    async def delete_property_enum_value(self, enum_id: int) -> bool:
        """
        Удаляет допустимое значение указателя. Нельзя удалить значение,
        которое уже проставлено хотя бы одному документу.
        """
        in_use = await db.execute_read(
            "SELECT 1 FROM document_property WHERE property_enum_id = %s", (enum_id,)
        )
        if in_use:
            raise ValueError("Значение используется в документах и не может быть удалено")

        rows_affected = await db.execute_write("DELETE FROM property_enum WHERE id = %s", (enum_id,))
        return rows_affected > 0
