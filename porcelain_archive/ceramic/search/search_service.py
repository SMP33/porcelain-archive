from __future__ import annotations

import html
import time
from datetime import date
from typing import Any

from porcelain_archive.database import db

PER_PAGE_DEFAULT = 30


class TTLCache:
    """Простейший одно-значный кэш с истечением по времени.

    Рассчитан на один процесс uvicorn (asyncio, без вытесняющего параллелизма):
    гонка между проверкой и установкой максимум приводит к лишнему пересчёту,
    что безопасно. Для многопроцессного деплоя нужен общий кэш (Redis и т.п.).
    """

    def __init__(self, ttl: float = 300.0) -> None:
        self.ttl = ttl
        self._value: Any | None = None
        self._expires: float = 0.0

    def get(self) -> Any | None:
        if self._value is not None and time.monotonic() < self._expires:
            return self._value
        return None

    def set(self, value: Any) -> None:
        self._value = value
        self._expires = time.monotonic() + self.ttl

    def invalidate(self) -> None:
        self._value = None
        self._expires = 0.0


# Фасеты поиска - заглушка (см. ниже): документы теперь общие с porcelain_archive
# (таблица document), у которой нет полей doc_type/authenticity/language/keywords/year,
# по которым раньше строились фасеты ceramic. Кэш оставлен для единообразия API.
facets_cache = TTLCache(ttl=300.0)

_EMPTY_FACETS = {
    "factories": [],
    "doc_types": [],
    "authenticities": [],
    "languages": [],
    "keywords": [],
    "properties": [],
    "year_min": 1900,
    "year_max": 2100,
}


class SearchService:
    async def get_facets(self) -> dict:
        # Фасеты «указателей» (property/property_enum): видимые указатели и их
        # значения, реально использованные видимыми документами (с количеством).
        rows = await db.execute_read(
            """
            SELECT p.id, p.title, pe.id, pe.value, COUNT(DISTINCT dp.document_id) AS cnt
            FROM property p
            JOIN property_enum pe ON pe.property_id = p.id
            JOIN document_property dp ON dp.property_enum_id = pe.id
            JOIN document d ON d.id = dp.document_id AND d.is_visible = 1
            WHERE p.is_visible = 1
            GROUP BY p.id, p.title, p.view_order, pe.id, pe.value
            ORDER BY p.view_order, p.id, pe.value
            """
        )
        props: dict = {}
        order: list = []
        for pid, ptitle, enum_id, value, cnt in rows:
            if pid not in props:
                props[pid] = {"id": pid, "title": ptitle, "values": []}
                order.append(pid)
            props[pid]["values"].append({"enum_id": enum_id, "value": value, "count": cnt})
        properties = [props[pid] for pid in order]
        return {**_EMPTY_FACETS, "year_max": date.today().year, "properties": properties}

    async def search(
        self,
        q: str,
        factory_id: int,
        doc_type: str,
        authenticity: str,
        language: str,
        keyword: str,
        year_from: int,
        year_to: int,
        offset: int,
        limit: int,
        pointers: list[int] | None = None,
    ) -> dict:
        # Поиск по названию документа (document.name, ILIKE) + фильтр по «указателям»
        # (property_enum через document_property). Остальные фильтры (doc_type и т.п.)
        # игнорируются - у общего с porcelain_archive document таких полей нет.
        conditions = ["is_visible = 1"]
        params: list = []
        if q.strip():
            conditions.append("name ILIKE %s")
            params.append(f"%{q.strip()}%")
        pointer_ids = sorted({int(p) for p in (pointers or []) if int(p) > 0})
        if pointer_ids:
            # Документ должен иметь ВСЕ выбранные значения указателей.
            conditions.append(
                "(SELECT COUNT(DISTINCT dp.property_enum_id) FROM document_property dp "
                "WHERE dp.document_id = document.id AND dp.property_enum_id = ANY(%s)) = %s"
            )
            params.append(pointer_ids)
            params.append(len(pointer_ids))
        where = " AND ".join(conditions)

        total_rows = await db.execute_read(f"SELECT COUNT(*) FROM document WHERE {where}", params)
        total = total_rows[0][0] if total_rows else 0

        rows = await db.execute_read(
            f"SELECT id, name FROM document WHERE {where} ORDER BY name LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )

        items = [
            {
                "id": r[0],
                "title": r[1],
                "doc_type": None,
                "doc_date": None,
                "year": None,
                "page_count": None,
                "factory_id": None,
                "factory_name": None,
                "thumb_url": None,
                "title_hl": html.escape(r[1] or ""),
                "snippet_hl": "",
            }
            for r in rows
        ]
        return {"items": items, "total": total}


search_service = SearchService()
