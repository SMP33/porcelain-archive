from __future__ import annotations

import html
import re
import time
from collections import Counter
from typing import Any

from porcelain_archive.ceramic.database import db
from porcelain_archive.ceramic.storage import get_storage

# Служебные маркеры подсветки: ts_headline вставляет их вокруг совпадений,
# после html.escape() безопасно заменяются на <mark> (защита от stored XSS -
# сам текст экранируется, разметку добавляют только наши сентинелы).
_HL_A = "\x02"
_HL_B = "\x03"
_HL_OPTS = f"StartSel={_HL_A},StopSel={_HL_B},HighlightAll=true"
_SNIPPET_OPTS = f"StartSel={_HL_A},StopSel={_HL_B},MaxWords=35,MinWords=15,ShortWord=3,HighlightAll=false"

_WORD_RE = re.compile(r"[^\W\d_]+|\d+", re.UNICODE)


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


# Фасеты поиска (списки заводов/типов/языков/ключевых слов, диапазон лет).
# Меняются только при правках в factory/document, инвалидируются оттуда.
facets_cache = TTLCache(ttl=300.0)

PER_PAGE_DEFAULT = 30


def _mark(value: str | None) -> str:
    if not value:
        return ""
    return html.escape(value).replace(_HL_A, "<mark>").replace(_HL_B, "</mark>")


def _tsquery(raw: str) -> str | None:
    words = _WORD_RE.findall(raw)
    if not words:
        return None
    return " & ".join(f"{w}:*" for w in words)


def _parse_keywords(rows: list[dict]) -> list[dict]:
    counter: Counter = Counter()
    for row in rows:
        if row["keywords"]:
            for kw in row["keywords"].split(","):
                kw = kw.strip()
                if kw:
                    counter[kw] += 1
    return [
        {"id": kw, "count": cnt}
        for kw, cnt in sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    ]


class SearchService:
    async def _compute_facets(self) -> dict:
        factories = await db.execute_read(
            """
            SELECT f.id, f.name, COUNT(d.id) AS count
            FROM factories f
            LEFT JOIN documents d ON d.factory_id = f.id AND d.page_count > 0
            GROUP BY f.id ORDER BY f.name
            """
        )
        doc_types = await db.execute_read(
            """
            SELECT doc_type AS id, COUNT(*) AS count FROM documents
            WHERE doc_type IS NOT NULL AND page_count > 0
            GROUP BY doc_type ORDER BY doc_type
            """
        )
        authenticities = await db.execute_read(
            """
            SELECT authenticity AS id, COUNT(*) AS count FROM documents
            WHERE authenticity IS NOT NULL AND page_count > 0
            GROUP BY authenticity ORDER BY authenticity
            """
        )
        languages = await db.execute_read(
            """
            SELECT language AS id, COUNT(*) AS count FROM documents
            WHERE language IS NOT NULL AND page_count > 0
            GROUP BY language ORDER BY language
            """
        )
        keyword_rows = await db.execute_read(
            "SELECT keywords FROM documents WHERE keywords IS NOT NULL AND keywords != '' AND page_count > 0"
        )
        year_row = await db.execute_read_one(
            "SELECT MIN(year) AS year_min, MAX(year) AS year_max FROM documents "
            "WHERE year IS NOT NULL AND page_count > 0"
        )

        return {
            "factories": factories,
            "doc_types": doc_types,
            "authenticities": authenticities,
            "languages": languages,
            "keywords": _parse_keywords(keyword_rows),
            "year_min": (year_row and year_row["year_min"]) or 1900,
            "year_max": (year_row and year_row["year_max"]) or 2100,
        }

    async def get_facets(self) -> dict:
        cached = facets_cache.get()
        if cached is not None:
            return cached
        facets = await self._compute_facets()
        facets_cache.set(facets)
        return facets

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
        storage = get_storage()
        conditions = ["d.page_count > 0"]
        params: list = []

        if factory_id:
            conditions.append("d.factory_id = %s")
            params.append(factory_id)
        if doc_type:
            conditions.append("d.doc_type = %s")
            params.append(doc_type)
        if authenticity:
            conditions.append("d.authenticity = %s")
            params.append(authenticity)
        if language:
            conditions.append("d.language = %s")
            params.append(language)
        if year_from:
            conditions.append("d.year >= %s")
            params.append(year_from)
        if year_to:
            conditions.append("d.year <= %s")
            params.append(year_to)
        if keyword:
            conditions.append(
                "EXISTS (SELECT 1 FROM unnest(string_to_array(d.keywords, ',')) kw WHERE trim(kw) = %s)"
            )
            params.append(keyword)

        tsquery = _tsquery(q) if q.strip() else None

        if tsquery:
            where = " AND ".join(conditions + ["d.search_vector @@ to_tsquery('russian', %s)"])
            query_params = [*params, tsquery]

            total_row = await db.execute_read_one(
                f"SELECT COUNT(*) AS cnt FROM documents d WHERE {where}", query_params
            )
            rows = await db.execute_read(
                f"""
                SELECT d.id, d.title, d.doc_type, d.doc_date, d.year, d.page_count,
                       d.factory_id, f.name AS factory_name, p.thumb_key,
                       ts_headline('russian', d.title, to_tsquery('russian', %s), %s) AS title_hl,
                       ts_headline('russian', coalesce(d.full_text, ''), to_tsquery('russian', %s), %s) AS snippet
                FROM documents d
                LEFT JOIN factories f ON f.id = d.factory_id
                LEFT JOIN pages p ON p.document_id = d.id AND p.page_number = 1
                WHERE {where}
                ORDER BY ts_rank_cd(d.search_vector, to_tsquery('russian', %s)) DESC
                LIMIT %s OFFSET %s
                """,
                [tsquery, _HL_OPTS, tsquery, _SNIPPET_OPTS, *query_params, tsquery, limit, offset],
            )
        else:
            where = " AND ".join(conditions)
            total_row = await db.execute_read_one(
                f"SELECT COUNT(*) AS cnt FROM documents d WHERE {where}", params
            )
            rows = await db.execute_read(
                f"""
                SELECT d.id, d.title, d.doc_type, d.doc_date, d.year, d.page_count,
                       d.factory_id, f.name AS factory_name, p.thumb_key,
                       NULL AS title_hl, NULL AS snippet
                FROM documents d
                LEFT JOIN factories f ON f.id = d.factory_id
                LEFT JOIN pages p ON p.document_id = d.id AND p.page_number = 1
                WHERE {where}
                ORDER BY d.doc_date DESC, d.title
                LIMIT %s OFFSET %s
                """,
                [*params, limit, offset],
            )

        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "title": r["title"],
                "doc_type": r["doc_type"],
                "doc_date": r["doc_date"],
                "year": r["year"],
                "page_count": r["page_count"],
                "factory_id": r["factory_id"],
                "factory_name": r["factory_name"],
                "thumb_url": storage.public_url(r["thumb_key"]) if r["thumb_key"] else None,
                "title_hl": _mark(r["title_hl"]) if r["title_hl"] else html.escape(r["title"] or ""),
                "snippet_hl": _mark(r["snippet"]) if r["snippet"] else "",
            })

        return {"items": items, "total": total_row["cnt"] if total_row else 0}


search_service = SearchService()
