from __future__ import annotations

from typing import Any, Optional, Sequence

from porcelain_archive.database import db
from porcelain_archive.document.document_service import DocumentService
from porcelain_archive.property.label import translated_label

# Объект (фарфоровое изделие) - обычный document с этим указателем, скрытый
# из общего поиска/списка "Материалы" (см. porcelain_archive/ceramic/search).
# Во всём остальном (страницы, ветки, ревью, указатели, описание, видимость)
# объект - обычный документ: создаётся, редактируется и получает фотографии
# через стандартный порядок работы с документами (см. porcelain_archive/document);
# этот модуль - только read-only витрина для публичного сайта/раздела /objects.
DOCUMENT_TYPE_TAG = "document_type"
OBJECT_TYPE_VALUE = "object"


class ObjectsService:
    def __init__(self) -> None:
        self._documents = DocumentService()

    async def _pointers_by_document(self, document_ids: Sequence[int]) -> dict[int, list[dict]]:
        """Видимые указатели объектов (кроме служебного document_type), по document_id."""
        if not document_ids:
            return {}
        rows = await db.execute_read(
            """
            SELECT dp.document_id, dp.tag, dp.value, p.id, p.title, p.type, pt.translated
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag AND p.is_visible = 1
            LEFT JOIN property_translate pt ON pt.tag = dp.tag AND pt.value = dp.value
            WHERE dp.document_id = ANY(%s)
            ORDER BY dp.document_id, p.view_order, p.id, dp.value
            """,
            (list(document_ids),),
        )
        grouped: dict[int, list[dict]] = {}
        for doc_id, tag, value, property_id, title, type_, translated in rows:
            label = translated_label(type_, value, translated, tag)
            grouped.setdefault(doc_id, []).append(
                {"pointer": f"{tag}:{value}", "value": label, "property_id": property_id, "property_title": title}
            )
        return grouped

    async def _covers_by_document(self, document_ids: Sequence[int]) -> dict[int, dict]:
        """Обложка (страница 1 master-ветки) и количество страниц, по document_id."""
        if not document_ids:
            return {}
        rows = await db.execute_read(
            """
            SELECT document.id, (b.meta->>'page_count')::int, pg.image_hash
            FROM document
            LEFT JOIN branch b ON b.document_id = document.id AND b.name = 'master'
            LEFT JOIN page pg ON pg.commit = b.last_commit AND pg.pos = 1
            WHERE document.id = ANY(%s)
            """,
            (list(document_ids),),
        )
        return {
            doc_id: {
                "page_count": page_count or 0,
                "cover_url": f"/api/ceramic/documents/{doc_id}/thumb" if image_hash else None,
            }
            for doc_id, page_count, image_hash in rows
        }

    async def list_objects(
        self, q: str = "", pointers: Optional[list[str]] = None, include_hidden: bool = False
    ) -> list[dict]:
        conditions = [
            "document.deleted = 0",
            "document.id IN (SELECT document_id FROM document_property WHERE tag = %s AND value = %s)",
        ]
        params: list[Any] = [DOCUMENT_TYPE_TAG, OBJECT_TYPE_VALUE]
        if not include_hidden:
            conditions.append("document.is_visible = 1")
        q = q.strip()
        if q:
            conditions.append("(document.name ILIKE %s OR document.meta->>'description' ILIKE %s)")
            params += [f"%{q}%", f"%{q}%"]
        pointer_keys = sorted({str(p) for p in (pointers or []) if p})
        if pointer_keys:
            # Объект должен иметь ВСЕ выбранные значения указателей.
            conditions.append(
                "(SELECT COUNT(DISTINCT dp.tag || ':' || dp.value) FROM document_property dp "
                "WHERE dp.document_id = document.id AND (dp.tag || ':' || dp.value) = ANY(%s)) = %s"
            )
            params += [pointer_keys, len(pointer_keys)]
        where = " AND ".join(conditions)

        rows = await db.execute_read(
            f"""
            SELECT document.id, document.name, document.meta->>'description', document.is_visible
            FROM document
            WHERE {where}
            ORDER BY document.name
            """,
            params,
        )
        ids = [r[0] for r in rows]
        pointers_map = await self._pointers_by_document(ids)
        covers_map = await self._covers_by_document(ids)
        return [
            {
                "id": doc_id,
                "name": name,
                "description": description,
                "is_visible": bool(is_visible),
                **covers_map.get(doc_id, {"page_count": 0, "cover_url": None}),
                "pointers": pointers_map.get(doc_id, []),
            }
            for doc_id, name, description, is_visible in rows
        ]

    async def get_facets(self) -> list[dict]:
        """Видимые указатели и их значения, использованные объектами (с количеством)."""
        rows = await db.execute_read(
            """
            SELECT p.id, p.tag, p.title, p.type, dp.value, pt.translated, COUNT(DISTINCT dp.document_id) AS cnt
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            LEFT JOIN property_translate pt ON pt.tag = dp.tag AND pt.value = dp.value
            JOIN document d ON d.id = dp.document_id AND d.is_visible = 1 AND d.deleted = 0
            WHERE p.is_visible = 1 AND dp.document_id IS NOT NULL
              AND d.id IN (SELECT document_id FROM document_property WHERE tag = %s AND value = %s)
            GROUP BY p.id, p.tag, p.title, p.type, p.view_order, dp.value, pt.translated
            ORDER BY p.view_order, p.id, dp.value
            """,
            (DOCUMENT_TYPE_TAG, OBJECT_TYPE_VALUE),
        )
        props: dict = {}
        order: list = []
        for pid, tag, title, type_, value, translated, cnt in rows:
            if pid not in props:
                props[pid] = {"id": pid, "title": title, "values": []}
                order.append(pid)
            label = translated_label(type_, value, translated, tag)
            props[pid]["values"].append({"pointer": f"{tag}:{value}", "value": label, "count": cnt})
        return [props[pid] for pid in order]

    async def get_object(self, document_id: int, include_hidden: bool = False) -> Optional[dict]:
        doc = await self._documents.get_document(document_id)
        if doc is None or not doc.get("is_object"):
            return None
        if not include_hidden and not doc["is_visible"]:
            return None

        branch_id = await self._documents.get_master_branch_id(document_id)
        page_count = await self._documents.get_branch_page_count(branch_id) if branch_id else 0
        images = [
            {
                "page": pos,
                "url": f"/api/documents/branches/{branch_id}/pages/{pos}/image",
                "thumb_url": f"/api/documents/branches/{branch_id}/pages/{pos}/image/preview",
            }
            for pos in range(1, page_count + 1)
        ]
        pointers = (await self._pointers_by_document([document_id])).get(document_id, [])

        return {
            "id": document_id,
            "name": doc["name"],
            "description": doc.get("description"),
            "is_visible": doc["is_visible"],
            "master_branch_id": branch_id,
            "page_count": page_count,
            "images": images,
            "cover_url": images[0]["url"] if images else None,
            "pointers": pointers,
        }


objects_service = ObjectsService()
