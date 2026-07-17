from __future__ import annotations

import asyncio
import os
import re
import uuid

from porcelain_archive.ceramic.database import db
from porcelain_archive.ceramic.pdf import extract_pages
from porcelain_archive.ceramic.storage import get_storage

_MIN_YEAR = 1700
_MAX_YEAR = 2100
_YEAR_RE = re.compile(r"\b(1[789]\d{2}|20\d{2}|21\d{2})\b")

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
PAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif", ".pdf"}

_DOC_FIELDS = (
    "factory_id", "title", "doc_type", "doc_date", "description", "author",
    "source_archive", "fund", "inventory_no", "case_no", "sheets",
    "authenticity", "language", "keywords", "geography",
)


def parse_year(doc_date: str | None) -> int | None:
    """Извлечь год из произвольной строки даты документа.

    Поддерживает ISO-даты ('1955-03-12'), русские записи ('12 марта 1955 г.'),
    диапазоны ('1955-1957' - первый год) и т.п. Возвращает первый 4-значный
    год в диапазоне 1700-2100 или None, если год не найден.
    """
    if not doc_date:
        return None
    for match in _YEAR_RE.finditer(doc_date):
        year = int(match.group(1))
        if _MIN_YEAR <= year <= _MAX_YEAR:
            return year
    return None


def _int_or_none(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean(value) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _allowed_upload(filename: str) -> bool:
    return os.path.splitext(filename or "")[1].lower() in PAGE_EXTS


class DocumentService:
    def _invalidate_search_cache(self) -> None:
        from porcelain_archive.ceramic.search.search_service import facets_cache
        facets_cache.invalidate()

    async def list_documents(self, factory_id: int | None, offset: int, limit: int) -> dict:
        storage = get_storage()
        params: list = []
        where = "WHERE d.page_count > 0"
        if factory_id:
            where += " AND d.factory_id = %s"
            params.append(factory_id)

        total_row = await db.execute_read_one(
            f"SELECT COUNT(*) AS cnt FROM documents d {where}", params
        )
        rows = await db.execute_read(
            f"""
            SELECT d.id, d.title, d.doc_type, d.doc_date, d.year, d.page_count,
                   f.id AS factory_id, f.name AS factory_name, p.thumb_key
            FROM documents d
            LEFT JOIN factories f ON f.id = d.factory_id
            LEFT JOIN pages p ON p.document_id = d.id AND p.page_number = 1
            {where}
            ORDER BY d.doc_date DESC, d.title
            LIMIT %s OFFSET %s
            """,
            [*params, limit, offset],
        )
        items = [self._row_to_list_item(r, storage) for r in rows]
        return {"items": items, "total": total_row["cnt"] if total_row else 0}

    def _row_to_list_item(self, row: dict, storage) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "doc_type": row["doc_type"],
            "doc_date": row["doc_date"],
            "year": row["year"],
            "factory_id": row["factory_id"],
            "factory_name": row.get("factory_name"),
            "page_count": row["page_count"],
            "thumb_url": storage.public_url(row["thumb_key"]) if row.get("thumb_key") else None,
        }

    async def get_document(self, document_id: int) -> dict | None:
        storage = get_storage()
        doc = await db.execute_read_one(
            """
            SELECT d.*, f.name AS factory_name, f.id AS factory_id
            FROM documents d
            LEFT JOIN factories f ON f.id = d.factory_id
            WHERE d.id = %s
            """,
            (document_id,),
        )
        if doc is None:
            return None

        page_rows = await db.execute_read(
            "SELECT page_number, storage_key, thumb_key, ocr_text FROM pages "
            "WHERE document_id = %s ORDER BY page_number",
            (document_id,),
        )
        pages = [
            {
                "page_number": r["page_number"],
                "image_url": storage.public_url(r["storage_key"]),
                "thumb_url": storage.public_url(r["thumb_key"]),
                "ocr_text": r["ocr_text"],
            }
            for r in page_rows
        ]

        related_items = []
        if doc["factory_id"]:
            related_rows = await db.execute_read(
                """
                SELECT d.id, d.title, d.doc_type, d.doc_date, d.year, d.page_count,
                       d.factory_id, p.thumb_key
                FROM documents d
                LEFT JOIN pages p ON p.document_id = d.id AND p.page_number = 1
                WHERE d.factory_id = %s AND d.id != %s AND d.page_count > 0
                ORDER BY d.doc_date, d.title
                LIMIT 6
                """,
                (doc["factory_id"], document_id),
            )
            related_items = [self._row_to_list_item(r, storage) for r in related_rows]

        return {
            "id": doc["id"],
            "title": doc["title"],
            "doc_type": doc["doc_type"],
            "doc_date": doc["doc_date"],
            "year": doc["year"],
            "description": doc["description"],
            "author": doc["author"],
            "source_archive": doc["source_archive"],
            "fund": doc["fund"],
            "inventory_no": doc["inventory_no"],
            "case_no": doc["case_no"],
            "sheets": doc["sheets"],
            "authenticity": doc["authenticity"],
            "language": doc["language"],
            "keywords": doc["keywords"],
            "geography": doc["geography"],
            "full_text": doc["full_text"],
            "page_count": doc["page_count"],
            "factory_id": doc["factory_id"],
            "factory_name": doc["factory_name"],
            "pages": pages,
            "related": related_items,
        }

    async def create_document(self, fields: dict) -> int:
        values = {k: _clean(fields.get(k)) for k in _DOC_FIELDS}
        values["factory_id"] = _int_or_none(fields.get("factory_id"))
        row = await db.execute_insert_returning(
            """
            INSERT INTO documents
                (factory_id, title, doc_type, doc_date, year, description, author,
                 source_archive, fund, inventory_no, case_no, sheets,
                 authenticity, language, keywords, geography)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                values["factory_id"], values["title"], values["doc_type"], values["doc_date"],
                parse_year(values["doc_date"]), values["description"], values["author"],
                values["source_archive"], values["fund"], values["inventory_no"],
                values["case_no"], values["sheets"], values["authenticity"],
                values["language"], values["keywords"], values["geography"],
            ),
        )
        self._invalidate_search_cache()
        return row["id"]

    async def update_document(self, document_id: int, fields: dict) -> None:
        values = {k: _clean(fields.get(k)) for k in _DOC_FIELDS}
        values["factory_id"] = _int_or_none(fields.get("factory_id"))
        await db.execute_write(
            """
            UPDATE documents SET
                factory_id=%s, title=%s, doc_type=%s, doc_date=%s, year=%s, description=%s,
                author=%s, source_archive=%s, fund=%s, inventory_no=%s, case_no=%s,
                sheets=%s, authenticity=%s, language=%s, keywords=%s, geography=%s
            WHERE id=%s
            """,
            (
                values["factory_id"], values["title"], values["doc_type"], values["doc_date"],
                parse_year(values["doc_date"]), values["description"], values["author"],
                values["source_archive"], values["fund"], values["inventory_no"],
                values["case_no"], values["sheets"], values["authenticity"],
                values["language"], values["keywords"], values["geography"],
                document_id,
            ),
        )
        self._invalidate_search_cache()

    async def delete_document(self, document_id: int) -> None:
        storage = get_storage()
        page_rows = await db.execute_read(
            "SELECT storage_key, thumb_key FROM pages WHERE document_id = %s", (document_id,)
        )
        for row in page_rows:
            for key in (row["storage_key"], row["thumb_key"]):
                try:
                    await asyncio.to_thread(storage.delete, key)
                except Exception:
                    pass
        await db.execute_write("DELETE FROM documents WHERE id = %s", (document_id,))
        self._invalidate_search_cache()

    async def list_pages(self, document_id: int) -> list[dict]:
        storage = get_storage()
        rows = await db.execute_read(
            "SELECT * FROM pages WHERE document_id = %s ORDER BY page_number", (document_id,)
        )
        return [
            {
                "page_number": r["page_number"],
                "image_url": storage.public_url(r["storage_key"]),
                "thumb_url": storage.public_url(r["thumb_key"]),
                "ocr_text": r["ocr_text"],
            }
            for r in rows
        ]

    async def _recompute_full_text(self, document_id: int) -> None:
        """Пересобрать documents.full_text из ocr_text страниц по порядку.
        full_text - производное поле, единственный потребитель - полнотекстовый
        поиск (search_vector пересчитывается триггером на UPDATE documents)."""
        rows = await db.execute_read(
            "SELECT ocr_text FROM pages WHERE document_id = %s ORDER BY page_number",
            (document_id,),
        )
        parts = [r["ocr_text"] for r in rows]
        full_text = "\n\n".join(p.strip() for p in parts if p and p.strip()) or None
        await db.execute_write(
            "UPDATE documents SET full_text = %s WHERE id = %s", (full_text, document_id)
        )

    async def upload_pages(self, document_id: int, files: list) -> list[dict]:
        exists = await db.execute_read_one("SELECT id FROM documents WHERE id = %s", (document_id,))
        if not exists:
            raise ValueError("not_found")

        storage = get_storage()

        def _sorted_files(fs):
            return sorted(fs, key=lambda f: f.filename or "")

        uploaded: list[tuple[str, str, str]] = []
        for upload in _sorted_files(files):
            if not upload.filename or not _allowed_upload(upload.filename):
                continue
            data = await upload.read()
            if not data or len(data) > MAX_UPLOAD_BYTES:
                continue
            ext = os.path.splitext(upload.filename)[1].lower()

            rendered = await asyncio.to_thread(
                extract_pages, data, ext, upload.content_type or ""
            )
            for jpeg_bytes, thumb_bytes, text in rendered:
                orig_key = f"pages/{document_id}/{uuid.uuid4().hex}.jpg"
                thumb_key = f"pages/{document_id}/thumb_{uuid.uuid4().hex}.jpg"
                await asyncio.to_thread(storage.upload, orig_key, jpeg_bytes, "image/jpeg")
                await asyncio.to_thread(storage.upload, thumb_key, thumb_bytes, "image/jpeg")
                uploaded.append((orig_key, thumb_key, text))

        if uploaded:
            max_row = await db.execute_read_one(
                "SELECT COALESCE(MAX(page_number), 0) AS max_num FROM pages WHERE document_id = %s",
                (document_id,),
            )
            page_num = max_row["max_num"] if max_row else 0
            for orig_key, thumb_key, text in uploaded:
                page_num += 1
                await db.execute_write(
                    "INSERT INTO pages (document_id, page_number, storage_key, thumb_key, ocr_text) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (document_id, page_num, orig_key, thumb_key, (text or "").strip() or None),
                )
            await db.execute_write(
                "UPDATE documents SET page_count = "
                "(SELECT COUNT(*) FROM pages WHERE document_id = %s) WHERE id = %s",
                (document_id, document_id),
            )
            await self._recompute_full_text(document_id)
            self._invalidate_search_cache()

        return await self.list_pages(document_id)

    async def delete_page(self, document_id: int, page_number: int) -> None:
        storage = get_storage()
        row = await db.execute_read_one(
            "SELECT storage_key, thumb_key FROM pages WHERE document_id = %s AND page_number = %s",
            (document_id, page_number),
        )
        if not row:
            return
        for key in (row["storage_key"], row["thumb_key"]):
            try:
                await asyncio.to_thread(storage.delete, key)
            except Exception:
                pass
        await db.execute_write(
            "DELETE FROM pages WHERE document_id = %s AND page_number = %s",
            (document_id, page_number),
        )
        remaining = await db.execute_read(
            "SELECT id FROM pages WHERE document_id = %s ORDER BY page_number", (document_id,)
        )
        for i, r in enumerate(remaining, 1):
            await db.execute_write("UPDATE pages SET page_number = %s WHERE id = %s", (i, r["id"]))
        await db.execute_write(
            "UPDATE documents SET page_count = %s WHERE id = %s", (len(remaining), document_id)
        )
        await self._recompute_full_text(document_id)
        self._invalidate_search_cache()

    async def update_pages_text(self, document_id: int, texts: dict[int, str]) -> None:
        existing_rows = await db.execute_read(
            "SELECT page_number FROM pages WHERE document_id = %s", (document_id,)
        )
        existing = {r["page_number"] for r in existing_rows}
        if not existing:
            raise ValueError("not_found")
        for page_number, text in texts.items():
            page_number = int(page_number)
            if page_number in existing:
                await db.execute_write(
                    "UPDATE pages SET ocr_text = %s WHERE document_id = %s AND page_number = %s",
                    (str(text).strip() or None, document_id, page_number),
                )
        await self._recompute_full_text(document_id)
        self._invalidate_search_cache()

    async def reorder_pages(self, document_id: int, order: list[int]) -> None:
        # Двухфазный UPDATE через временные номера - иначе UNIQUE(document_id, page_number)
        # конфликтует при пересечении старых и новых номеров.
        for i, orig_num in enumerate(order):
            await db.execute_write(
                "UPDATE pages SET page_number = %s WHERE document_id = %s AND page_number = %s",
                (10000 + i + 1, document_id, orig_num),
            )
        for i in range(len(order)):
            await db.execute_write(
                "UPDATE pages SET page_number = %s WHERE document_id = %s AND page_number = %s",
                (i + 1, document_id, 10000 + i + 1),
            )

    async def sitemap_document_ids(self) -> list[int]:
        rows = await db.execute_read(
            "SELECT id FROM documents WHERE page_count > 0 ORDER BY id"
        )
        return [r["id"] for r in rows]

    async def admin_list(self, q: str, factory_id: int, issues: str, offset: int, limit: int) -> dict:
        conditions = []
        params: list = []
        if q.strip():
            conditions.append("d.title ILIKE %s")
            params.append(f"%{q.strip()}%")
        if factory_id:
            conditions.append("d.factory_id = %s")
            params.append(factory_id)
        if issues == "no_factory":
            conditions.append("d.factory_id IS NULL")
        elif issues == "no_pages":
            conditions.append("d.page_count = 0")
        elif issues == "any":
            conditions.append("(d.factory_id IS NULL OR d.page_count = 0)")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        total_row = await db.execute_read_one(f"SELECT COUNT(*) AS cnt FROM documents d {where}", params)
        rows = await db.execute_read(
            f"""
            SELECT d.id, d.title, d.doc_type, d.doc_date, d.page_count, d.factory_id,
                   f.name AS factory_name
            FROM documents d
            LEFT JOIN factories f ON f.id = d.factory_id
            {where}
            ORDER BY d.id DESC
            LIMIT %s OFFSET %s
            """,
            [*params, limit, offset],
        )
        return {"items": rows, "total": total_row["cnt"] if total_row else 0}


document_service = DocumentService()
