from __future__ import annotations

from typing import Optional

from porcelain_archive.ceramic.database import db as ceramic_db
from porcelain_archive.ceramic.storage import storage

IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_COVER_BYTES = 10 * 1024 * 1024


def _int_or_none(value) -> Optional[int]:
    """Год как int или None (нечисловое/пустое -> None)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _validate_cover(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in IMAGE_EXTS:
        raise ValueError("Недопустимый формат изображения (нужен jpg/png/webp/gif)")
    if len(data) > MAX_COVER_BYTES:
        raise ValueError("Изображение слишком большое (максимум 10 МБ)")
    return ext


class FactoriesService:
    def _to_public(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "founded": row["founded"],
            "closed": row["closed"],
            "notes": row.get("notes"),
            "doc_count": row.get("doc_count", 0),
            "cover_url": storage.url(row.get("cover_key")),
        }

    async def list_factories(self) -> list[dict]:
        rows = await ceramic_db.execute_read(
            """
            SELECT f.id, f.name, f.location, f.founded, f.closed, f.notes, f.cover_key,
                   (SELECT COUNT(*) FROM document d
                      WHERE d.is_visible = 1
                        AND (d.meta->>'factory_id')::bigint = f.id) AS doc_count
            FROM factory f
            ORDER BY f.name
            """
        )
        return [self._to_public(r) for r in rows]

    async def get_factory(self, factory_id: int, offset: int = 0, limit: int = 24) -> Optional[dict]:
        row = await ceramic_db.execute_read_one(
            "SELECT id, name, location, founded, closed, notes, cover_key FROM factory WHERE id = %s",
            (factory_id,),
        )
        if row is None:
            return None
        total_row = await ceramic_db.execute_read_one(
            "SELECT COUNT(*) AS n FROM document WHERE is_visible = 1 AND (meta->>'factory_id')::bigint = %s",
            (factory_id,),
        )
        total = total_row["n"] if total_row else 0
        docs = await ceramic_db.execute_read(
            """
            SELECT id, name FROM document
            WHERE is_visible = 1 AND (meta->>'factory_id')::bigint = %s
            ORDER BY name
            LIMIT %s OFFSET %s
            """,
            (factory_id, limit, offset),
        )
        result = self._to_public(row)
        result["documents"] = [{"id": d["id"], "title": d["name"]} for d in docs]
        result["total"] = total
        return result

    async def create_factory(
        self, name: str, location: str, founded, closed, notes: str,
        cover_filename: Optional[str], cover_data: Optional[bytes],
    ) -> int:
        name = (name or "").strip()
        if not name:
            raise ValueError("Название объекта обязательно")
        cover_key = None
        if cover_data:
            ext = _validate_cover(cover_filename or "", cover_data)
            cover_key = storage.save_image(cover_data, ext)
        row = await ceramic_db.execute_insert_returning(
            """
            INSERT INTO factory (name, location, founded, closed, notes, cover_key)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (name, (location or "").strip() or None, _int_or_none(founded),
             _int_or_none(closed), (notes or "").strip() or None, cover_key),
        )
        return row["id"]

    async def update_factory(
        self, factory_id: int, name: str, location: str, founded, closed, notes: str,
        cover_filename: Optional[str], cover_data: Optional[bytes], remove_cover: bool,
    ) -> bool:
        existing = await ceramic_db.execute_read_one(
            "SELECT cover_key FROM factory WHERE id = %s", (factory_id,)
        )
        if existing is None:
            return False
        name = (name or "").strip()
        if not name:
            raise ValueError("Название объекта обязательно")

        cover_key = existing["cover_key"]
        if cover_data:
            ext = _validate_cover(cover_filename or "", cover_data)
            new_key = storage.save_image(cover_data, ext)
            storage.delete(cover_key)
            cover_key = new_key
        elif remove_cover:
            storage.delete(cover_key)
            cover_key = None

        await ceramic_db.execute_write(
            """
            UPDATE factory SET name=%s, location=%s, founded=%s, closed=%s, notes=%s, cover_key=%s
            WHERE id=%s
            """,
            (name, (location or "").strip() or None, _int_or_none(founded),
             _int_or_none(closed), (notes or "").strip() or None, cover_key, factory_id),
        )
        return True

    async def delete_factory(self, factory_id: int) -> bool:
        existing = await ceramic_db.execute_read_one(
            "SELECT cover_key FROM factory WHERE id = %s", (factory_id,)
        )
        if existing is None:
            return False
        storage.delete(existing["cover_key"])
        # Отвязываем документы (снимаем factory_id из meta), чтобы не осталось битых ссылок.
        await ceramic_db.execute_write(
            "UPDATE document SET meta = meta - 'factory_id' WHERE (meta->>'factory_id')::bigint = %s",
            (factory_id,),
        )
        await ceramic_db.execute_write("DELETE FROM factory WHERE id = %s", (factory_id,))
        return True


factories_service = FactoriesService()
