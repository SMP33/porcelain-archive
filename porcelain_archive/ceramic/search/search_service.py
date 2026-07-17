from __future__ import annotations

import html
import time
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
    "year_min": 1900,
    "year_max": 2100,
}


class SearchService:
    async def get_facets(self) -> dict:
        # Заглушка - см. комментарий у facets_cache.
        return _EMPTY_FACETS

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
    ) -> dict:
        # Заглушка: только поиск по названию документа (document.name, ILIKE).
        # Фильтры factory_id/doc_type/authenticity/language/keyword/year_from/year_to
        # игнорируются - у общего с porcelain_archive document таких полей нет.
        conditions = ["is_visible = 1"]
        params: list = []
        if q.strip():
            conditions.append("name ILIKE %s")
            params.append(f"%{q.strip()}%")
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
