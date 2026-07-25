from __future__ import annotations

from datetime import date

from porcelain_archive.database import db

PER_PAGE_DEFAULT = 30

DEFAULT_YEAR_MIN = 1900

# Документы-объекты (см. porcelain_archive/ceramic/objects) - обычные document
# с этим указателем, скрытые из общего поиска/списка "Материалы" - видны только
# через отдельные /objects.
DOCUMENT_TYPE_TAG = "document_type"
OBJECT_TYPE_VALUE = "object"


class SearchService:
    async def get_facets(self) -> dict:
        # Фасеты «указателей» (property/document_property): видимые указатели и их
        # значения, реально использованные видимыми документами-не-объектами (с количеством).
        rows = await db.execute_read(
            """
            SELECT p.id, p.tag, p.title, p.type, dp.value, COUNT(DISTINCT dp.document_id) AS cnt
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag
            JOIN document d ON d.id = dp.document_id AND d.is_visible = 1
            WHERE p.is_visible = 1 AND dp.document_id IS NOT NULL
              AND d.id NOT IN (
                  SELECT document_id FROM document_property
                  WHERE tag = %s AND value = %s
              )
            GROUP BY p.id, p.tag, p.title, p.type, p.view_order, dp.value
            ORDER BY p.view_order, p.id, dp.value
            """,
            (DOCUMENT_TYPE_TAG, OBJECT_TYPE_VALUE),
        )
        props: dict = {}
        order: list = []
        for pid, tag, ptitle, type_, value, cnt in rows:
            if pid not in props:
                props[pid] = {"id": pid, "title": ptitle, "values": []}
                order.append(pid)
            label = ("Да" if value == "true" else "Нет") if type_ == "bool" else value
            props[pid]["values"].append({"pointer": f"{tag}:{value}", "value": label, "count": cnt})
        properties = [props[pid] for pid in order]

        # Границы периода - по фактическим датам видимых документов (не объектов).
        year_rows = await db.execute_read(
            """
            SELECT MIN(LEFT(meta->>'date_from', 4)::int), MAX(LEFT(COALESCE(meta->>'date_to', meta->>'date_from'), 4)::int)
            FROM document
            WHERE is_visible = 1 AND deleted = 0 AND meta->>'date_from' ~ '^\\d{4}'
              AND id NOT IN (
                  SELECT document_id FROM document_property
                  WHERE tag = %s AND value = %s
              )
            """,
            (DOCUMENT_TYPE_TAG, OBJECT_TYPE_VALUE),
        )
        year_min, year_max = (year_rows[0] if year_rows else (None, None))
        return {
            "properties": properties,
            "year_min": year_min or DEFAULT_YEAR_MIN,
            "year_max": year_max or date.today().year,
        }

    async def search(
        self,
        q: str,
        year_from: int,
        year_to: int,
        offset: int,
        limit: int,
        pointers: list[str] | None = None,
    ) -> dict:
        # Поиск по названию и описанию документа + фильтры по указателям и датам.
        # Документы-объекты (document_type=object) в выдачу не попадают - у них
        # отдельные страницы /objects.
        conditions = [
            "document.is_visible = 1",
            "document.deleted = 0",
            "document.id NOT IN (SELECT document_id FROM document_property WHERE tag = %s AND value = %s)",
        ]
        params: list = [DOCUMENT_TYPE_TAG, OBJECT_TYPE_VALUE]
        if q.strip():
            conditions.append("(document.name ILIKE %s OR document.meta->>'description' ILIKE %s)")
            params += [f"%{q.strip()}%", f"%{q.strip()}%"]
        # Документ попадает в период, если его интервал пересекается с выбранным.
        # Проверка ~ '^\d{4}' обязательна: без неё документ с нечисловой датой
        # (данные заводились и вручную) роняет запрос на ::int.
        if year_from or year_to:
            conditions.append("document.meta->>'date_from' ~ '^[0-9]{4}'")
        if year_from:
            conditions.append(
                "LEFT(COALESCE(NULLIF(document.meta->>'date_to', ''), document.meta->>'date_from'), 4)"
                " ~ '^[0-9]{4}' AND"
                " LEFT(COALESCE(NULLIF(document.meta->>'date_to', ''), document.meta->>'date_from'), 4)::int >= %s"
            )
            params.append(int(year_from))
        if year_to:
            conditions.append("LEFT(document.meta->>'date_from', 4)::int <= %s")
            params.append(int(year_to))
        # pointer - строка "tag:value", однозначно определяющая допустимое значение указателя.
        pointer_keys = sorted({str(p) for p in (pointers or []) if p})
        if pointer_keys:
            # Документ должен иметь ВСЕ выбранные значения указателей.
            conditions.append(
                "(SELECT COUNT(DISTINCT dp.tag || ':' || dp.value) FROM document_property dp "
                "WHERE dp.document_id = document.id AND (dp.tag || ':' || dp.value) = ANY(%s)) = %s"
            )
            params.append(pointer_keys)
            params.append(len(pointer_keys))
        where = " AND ".join(conditions)

        total_rows = await db.execute_read(f"SELECT COUNT(*) FROM document WHERE {where}", params)
        total = total_rows[0][0] if total_rows else 0

        rows = await db.execute_read(
            f"""
            SELECT document.id, document.name, document.meta->>'description',
                   (b.meta->>'page_count')::int, pg.image_hash,
                   document.meta->>'date_from', document.meta->>'date_to'
            FROM document
            LEFT JOIN branch b ON b.document_id = document.id AND b.name = 'master'
            LEFT JOIN page pg ON pg.commit = b.last_commit AND pg.pos = 1
            WHERE {where} ORDER BY document.name LIMIT %s OFFSET %s
            """,
            [*params, limit, offset],
        )

        pointers_map = await self._pointers_by_document([r[0] for r in rows])

        items = [
            {
                "id": r[0],
                "title": r[1],
                "date_from": r[5],
                "date_to": r[6],
                "page_count": r[3],
                "thumb_url": f"/api/ceramic/documents/{r[0]}/thumb" if r[4] else None,
                "pointers": pointers_map.get(r[0], []),
                "description": r[2],
            }
            for r in rows
        ]
        return {"items": items, "total": total}

    async def _pointers_by_document(self, doc_ids: list[int]) -> dict[int, list[dict]]:
        """Видимые указатели документов, сгруппированные по document_id."""
        if not doc_ids:
            return {}
        rows = await db.execute_read(
            """
            SELECT dp.document_id, dp.tag, dp.value, p.id, p.title
            FROM document_property dp
            JOIN property p ON p.tag = dp.tag AND p.is_visible = 1
            WHERE dp.document_id = ANY(%s)
            ORDER BY dp.document_id, p.view_order, p.id, dp.value
            """,
            (doc_ids,),
        )
        grouped: dict[int, list[dict]] = {}
        for doc_id, tag, value, property_id, title in rows:
            grouped.setdefault(doc_id, []).append(
                {"pointer": f"{tag}:{value}", "value": value, "property_id": property_id, "property_title": title}
            )
        return grouped


search_service = SearchService()
