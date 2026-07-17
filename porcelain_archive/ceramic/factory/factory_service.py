from __future__ import annotations

import asyncio
import os
import uuid

from porcelain_archive.ceramic.database import db
from porcelain_archive.ceramic.storage import get_storage

MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _int_or_none(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _allowed_image(filename: str) -> bool:
    return os.path.splitext(filename or "")[1].lower() in IMAGE_EXTS


class FactoryService:
    def _row_to_item(self, row: dict, storage) -> dict:
        return {
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "founded": row["founded"],
            "closed": row["closed"],
            "cover_url": storage.public_url(row["image_key"]) if row.get("image_key") else None,
            "doc_count": row.get("doc_count", 0),
        }

    async def list_factories(self, offset: int, limit: int) -> dict:
        storage = get_storage()
        total_row = await db.execute_read_one("SELECT COUNT(*) AS cnt FROM factories")
        rows = await db.execute_read(
            """
            SELECT f.*, COUNT(d.id) FILTER (WHERE d.page_count > 0) AS doc_count
            FROM factories f
            LEFT JOIN documents d ON d.factory_id = f.id
            GROUP BY f.id ORDER BY f.name
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return {
            "items": [self._row_to_item(r, storage) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
        }

    async def list_recent(self, limit: int) -> list[dict]:
        storage = get_storage()
        rows = await db.execute_read(
            """
            SELECT f.*, COUNT(d.id) FILTER (WHERE d.page_count > 0) AS doc_count
            FROM factories f
            LEFT JOIN documents d ON d.factory_id = f.id
            GROUP BY f.id ORDER BY f.id DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [self._row_to_item(r, storage) for r in rows]

    async def get_factory(self, factory_id: int) -> dict | None:
        storage = get_storage()
        row = await db.execute_read_one("SELECT * FROM factories WHERE id = %s", (factory_id,))
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "founded": row["founded"],
            "closed": row["closed"],
            "notes": row["notes"],
            "cover_url": storage.public_url(row["image_key"]) if row["image_key"] else None,
        }

    async def list_documents(self, factory_id: int, offset: int, limit: int) -> dict:
        storage = get_storage()
        total_row = await db.execute_read_one(
            "SELECT COUNT(*) AS cnt FROM documents WHERE factory_id = %s AND page_count > 0",
            (factory_id,),
        )
        rows = await db.execute_read(
            """
            SELECT d.id, d.title, d.doc_type, d.doc_date, d.year, d.page_count,
                   p.thumb_key
            FROM documents d
            LEFT JOIN pages p ON p.document_id = d.id AND p.page_number = 1
            WHERE d.factory_id = %s AND d.page_count > 0
            ORDER BY d.doc_date, d.title
            LIMIT %s OFFSET %s
            """,
            (factory_id, limit, offset),
        )
        items = [
            {
                "id": r["id"],
                "title": r["title"],
                "doc_type": r["doc_type"],
                "doc_date": r["doc_date"],
                "year": r["year"],
                "page_count": r["page_count"],
                "factory_id": factory_id,
                "thumb_url": storage.public_url(r["thumb_key"]) if r["thumb_key"] else None,
            }
            for r in rows
        ]
        return {"items": items, "total": total_row["cnt"] if total_row else 0}

    async def _upload_cover(self, filename: str, content_type: str, data: bytes) -> str | None:
        if not filename or not _allowed_image(filename) or not data or len(data) > MAX_IMAGE_BYTES:
            return None
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        key = f"covers/{uuid.uuid4().hex}{ext}"
        await asyncio.to_thread(get_storage().upload, key, data, content_type or "image/jpeg")
        return key

    def _invalidate_search_cache(self) -> None:
        from porcelain_archive.ceramic.search.search_service import facets_cache
        facets_cache.invalidate()

    async def create_factory(self, fields: dict, image_file) -> int:
        image_key = None
        if image_file is not None and image_file.filename:
            data = await image_file.read()
            image_key = await self._upload_cover(image_file.filename, image_file.content_type, data)

        row = await db.execute_insert_returning(
            """
            INSERT INTO factories (name, location, founded, closed, notes, image_key)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (
                fields["name"].strip(),
                (fields.get("location") or "").strip() or None,
                _int_or_none(fields.get("founded")),
                _int_or_none(fields.get("closed")),
                (fields.get("notes") or "").strip() or None,
                image_key,
            ),
        )
        self._invalidate_search_cache()
        return row["id"]

    async def update_factory(self, factory_id: int, fields: dict, image_file) -> None:
        row = await db.execute_read_one("SELECT image_key FROM factories WHERE id = %s", (factory_id,))
        if row is None:
            raise ValueError("not_found")
        image_key = row["image_key"]

        if image_file is not None and image_file.filename:
            data = await image_file.read()
            new_key = await self._upload_cover(image_file.filename, image_file.content_type, data)
            if new_key:
                if image_key:
                    try:
                        await asyncio.to_thread(get_storage().delete, image_key)
                    except Exception:
                        pass
                image_key = new_key

        await db.execute_write(
            """
            UPDATE factories SET name=%s, location=%s, founded=%s, closed=%s, notes=%s, image_key=%s
            WHERE id=%s
            """,
            (
                fields["name"].strip(),
                (fields.get("location") or "").strip() or None,
                _int_or_none(fields.get("founded")),
                _int_or_none(fields.get("closed")),
                (fields.get("notes") or "").strip() or None,
                image_key,
                factory_id,
            ),
        )
        self._invalidate_search_cache()

    async def delete_factory(self, factory_id: int) -> None:
        row = await db.execute_read_one("SELECT image_key FROM factories WHERE id = %s", (factory_id,))
        if row and row["image_key"]:
            try:
                await asyncio.to_thread(get_storage().delete, row["image_key"])
            except Exception:
                pass
        await db.execute_write("DELETE FROM factories WHERE id = %s", (factory_id,))
        self._invalidate_search_cache()

    async def delete_cover(self, factory_id: int) -> None:
        row = await db.execute_read_one("SELECT image_key FROM factories WHERE id = %s", (factory_id,))
        if row and row["image_key"]:
            try:
                await asyncio.to_thread(get_storage().delete, row["image_key"])
            except Exception:
                pass
            await db.execute_write("UPDATE factories SET image_key = NULL WHERE id = %s", (factory_id,))

    async def stats(self) -> dict:
        row = await db.execute_read_one(
            """
            SELECT
                (SELECT COUNT(*) FROM factories) AS factory_count,
                COALESCE(SUM(CASE WHEN page_count > 0 THEN 1 ELSE 0 END), 0) AS doc_count,
                COALESCE(SUM(CASE WHEN page_count > 0 THEN page_count ELSE 0 END), 0) AS page_count
            FROM documents
            """
        )
        return dict(row) if row else {"factory_count": 0, "doc_count": 0, "page_count": 0}


factory_service = FactoryService()
