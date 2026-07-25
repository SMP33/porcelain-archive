from __future__ import annotations

from typing import Optional, Sequence

from porcelain_archive.database import db
from porcelain_archive.ceramic.storage import storage

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _validate_image(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in IMAGE_EXTS:
        raise ValueError("Недопустимый формат изображения (нужен jpg/png/webp/gif)")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Изображение слишком большое (максимум 10 МБ)")
    return ext


class ObjectsService:
    async def _images_by_object(self, object_ids: Sequence[int]) -> dict[int, list[dict]]:
        """Фотографии объектов, сгруппированные по object_id (в порядке sort_order)."""
        if not object_ids:
            return {}
        rows = await db.execute_read_dict(
            "SELECT id, object_id, image_key FROM object_image "
            "WHERE object_id = ANY(%s) ORDER BY object_id, sort_order, id",
            (list(object_ids),),
        )
        grouped: dict[int, list[dict]] = {}
        for r in rows:
            grouped.setdefault(r["object_id"], []).append(
                {"id": r["id"], "url": storage.url(r["image_key"])}
            )
        return grouped

    async def _pointers_by_object(self, object_ids: Sequence[int]) -> dict[int, list[dict]]:
        """Указатели объектов, сгруппированные по object_id."""
        if not object_ids:
            return {}
        rows = await db.execute_read_dict(
            """
            SELECT op.object_id, pe.id AS enum_id, pe.value, p.id AS property_id, p.title
            FROM object_property op
            JOIN property_enum pe ON pe.id = op.property_enum_id
            JOIN property p ON p.id = pe.property_id AND p.is_visible = 1
            WHERE op.object_id = ANY(%s)
            ORDER BY op.object_id, p.view_order, p.id, pe.value
            """,
            (list(object_ids),),
        )
        grouped: dict[int, list[dict]] = {}
        for r in rows:
            grouped.setdefault(r["object_id"], []).append(
                {
                    "enum_id": r["enum_id"],
                    "value": r["value"],
                    "property_id": r["property_id"],
                    "property_title": r["title"],
                }
            )
        return grouped

    def _to_public(self, row: dict, images: list[dict], pointers: list[dict]) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "notes": row.get("notes"),
            "images": images,
            "cover_url": images[0]["url"] if images else None,
            "pointers": pointers,
            "is_visible": bool(row.get("is_visible", 1)),
        }

    async def list_objects(
        self, q: str = "", pointers: Optional[list[int]] = None, include_hidden: bool = False
    ) -> list[dict]:
        conditions: list[str] = []
        params: list = []
        if not include_hidden:
            conditions.append("o.is_visible = 1")
        q = q.strip()
        if q:
            conditions.append("(o.name ILIKE %s OR o.notes ILIKE %s)")
            params += [f"%{q}%", f"%{q}%"]
        pointer_ids = sorted({int(p) for p in (pointers or []) if int(p) > 0})
        if pointer_ids:
            # Объект должен иметь ВСЕ выбранные значения указателей.
            conditions.append(
                "(SELECT COUNT(*) FROM object_property op "
                "WHERE op.object_id = o.id AND op.property_enum_id = ANY(%s)) = %s"
            )
            params += [pointer_ids, len(pointer_ids)]
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = await db.execute_read_dict(
            f"SELECT o.id, o.name, o.notes, o.is_visible FROM porcelain_object o {where} ORDER BY o.name",
            params,
        )
        ids = [r["id"] for r in rows]
        images = await self._images_by_object(ids)
        pointer_map = await self._pointers_by_object(ids)
        return [
            self._to_public(r, images.get(r["id"], []), pointer_map.get(r["id"], []))
            for r in rows
        ]

    async def get_object(self, object_id: int, include_hidden: bool = False) -> Optional[dict]:
        row = await db.execute_read_one_dict(
            "SELECT id, name, notes, is_visible FROM porcelain_object WHERE id = %s", (object_id,)
        )
        if row is None or (not include_hidden and not row["is_visible"]):
            return None
        images = await self._images_by_object([object_id])
        pointers = await self._pointers_by_object([object_id])
        return self._to_public(row, images.get(object_id, []), pointers.get(object_id, []))

    async def get_facets(self) -> list[dict]:
        """Видимые указатели и их значения, использованные объектами (с количеством)."""
        rows = await db.execute_read_dict(
            """
            SELECT p.id AS property_id, p.title, pe.id AS enum_id, pe.value,
                   COUNT(DISTINCT o.id) AS cnt
            FROM property p
            JOIN property_enum pe ON pe.property_id = p.id
            JOIN object_property op ON op.property_enum_id = pe.id
            JOIN porcelain_object o ON o.id = op.object_id AND o.is_visible = 1
            WHERE p.is_visible = 1
            GROUP BY p.id, p.title, p.view_order, pe.id, pe.value
            ORDER BY p.view_order, p.id, pe.value
            """
        )
        props: dict = {}
        order: list = []
        for r in rows:
            pid = r["property_id"]
            if pid not in props:
                props[pid] = {"id": pid, "title": r["title"], "values": []}
                order.append(pid)
            props[pid]["values"].append(
                {"enum_id": r["enum_id"], "value": r["value"], "count": r["cnt"]}
            )
        return [props[pid] for pid in order]

    async def list_available_pointers(self) -> list[dict]:
        """Все указатели и их значения, доступные для назначения объекту."""
        rows = await db.execute_read_dict(
            """
            SELECT p.id AS property_id, p.title, pe.id AS enum_id, pe.value
            FROM property p
            JOIN property_enum pe ON pe.property_id = p.id
            WHERE pe.is_pointer = 1
            ORDER BY p.view_order, p.id, pe.value
            """
        )
        props: dict = {}
        order: list = []
        for r in rows:
            pid = r["property_id"]
            if pid not in props:
                props[pid] = {"id": pid, "title": r["title"], "values": []}
                order.append(pid)
            props[pid]["values"].append({"enum_id": r["enum_id"], "value": r["value"]})
        return [props[pid] for pid in order]

    async def _set_pointers(self, object_id: int, pointers: Optional[list[int]]) -> None:
        await db.execute_write(
            "DELETE FROM object_property WHERE object_id = %s", (object_id,)
        )
        enum_ids = sorted({int(p) for p in (pointers or []) if int(p) > 0})
        for enum_id in enum_ids:
            await db.execute_write(
                "INSERT INTO object_property (object_id, property_enum_id) VALUES (%s, %s) "
                "ON CONFLICT DO NOTHING",
                (object_id, enum_id),
            )

    async def create_object(
        self, name: str, notes: str, pointers: Optional[list[int]],
        images: Optional[list[tuple[str, bytes]]] = None, is_visible: bool = True,
    ) -> int:
        name = (name or "").strip()
        if not name:
            raise ValueError("Название объекта обязательно")
        for filename, data in images or []:
            _validate_image(filename, data)
        row = await db.execute_insert_returning_dict(
            "INSERT INTO porcelain_object (name, notes, is_visible) VALUES (%s, %s, %s) RETURNING id",
            (name, (notes or "").strip() or None, int(is_visible)),
        )
        object_id = row["id"]
        await self._set_pointers(object_id, pointers)
        if images:
            await self.add_images(object_id, images)
        return object_id

    async def update_object(
        self, object_id: int, name: str, notes: str, pointers: Optional[list[int]],
        is_visible: bool = True,
    ) -> bool:
        exists = await db.execute_read_one_dict(
            "SELECT id FROM porcelain_object WHERE id = %s", (object_id,)
        )
        if exists is None:
            return False
        name = (name or "").strip()
        if not name:
            raise ValueError("Название объекта обязательно")
        await db.execute_write(
            "UPDATE porcelain_object SET name=%s, notes=%s, is_visible=%s WHERE id=%s",
            (name, (notes or "").strip() or None, int(is_visible), object_id),
        )
        await self._set_pointers(object_id, pointers)
        return True

    async def delete_object(self, object_id: int) -> bool:
        rows = await db.execute_read_dict(
            "SELECT image_key FROM object_image WHERE object_id = %s", (object_id,)
        )
        deleted = await db.execute_write(
            "DELETE FROM porcelain_object WHERE id = %s", (object_id,)
        )
        if not deleted:
            return False
        for r in rows:
            storage.delete(r["image_key"])
        return True

    async def add_images(
        self, object_id: int, images: list[tuple[str, bytes]]
    ) -> Optional[list[dict]]:
        """Добавляет фотографии в конец галереи объекта (None - объекта нет)."""
        exists = await db.execute_read_one_dict(
            "SELECT id FROM porcelain_object WHERE id = %s", (object_id,)
        )
        if exists is None:
            return None
        prepared = [(_validate_image(filename, data), data) for filename, data in images]
        row = await db.execute_read_one_dict(
            "SELECT COALESCE(MAX(sort_order), -1) AS max_order FROM object_image WHERE object_id = %s",
            (object_id,),
        )
        next_order = (row["max_order"] if row else -1) + 1
        for ext, data in prepared:
            key = storage.save_image(data, ext, prefix="objects")
            await db.execute_write(
                "INSERT INTO object_image (object_id, image_key, sort_order) VALUES (%s, %s, %s)",
                (object_id, key, next_order),
            )
            next_order += 1
        return (await self._images_by_object([object_id])).get(object_id, [])

    async def delete_image(self, object_id: int, image_id: int) -> bool:
        row = await db.execute_read_one_dict(
            "SELECT image_key FROM object_image WHERE id = %s AND object_id = %s",
            (image_id, object_id),
        )
        if row is None:
            return False
        await db.execute_write("DELETE FROM object_image WHERE id = %s", (image_id,))
        storage.delete(row["image_key"])
        return True

    async def reorder_images(self, object_id: int, image_ids: list[int]) -> bool:
        """Порядок фотографий по списку id (первая - обложка)."""
        rows = await db.execute_read_dict(
            "SELECT id FROM object_image WHERE object_id = %s", (object_id,)
        )
        known = {r["id"] for r in rows}
        if not known or {int(i) for i in image_ids} != known:
            return False
        for order, image_id in enumerate(image_ids):
            await db.execute_write(
                "UPDATE object_image SET sort_order = %s WHERE id = %s AND object_id = %s",
                (order, int(image_id), object_id),
            )
        return True


objects_service = ObjectsService()
