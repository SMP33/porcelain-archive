from __future__ import annotations

from fastapi import APIRouter, Query

from .search_service import PER_PAGE_DEFAULT, search_service

router = APIRouter(prefix="/api/ceramic/search", tags=["search"])


@router.get("")
@router.get("/")
async def search(
    q: str = "",
    factory_id: int = Query(0, ge=0),
    doc_type: str = "",
    authenticity: str = "",
    language: str = "",
    keyword: str = "",
    year_from: int = Query(0, ge=0),
    year_to: int = Query(0, ge=0),
    pointer: list[int] = Query(default=[]),
    offset: int = 0,
    limit: int = PER_PAGE_DEFAULT,
):
    return await search_service.search(
        q, factory_id, doc_type, authenticity, language, keyword, year_from, year_to, offset, limit, pointer
    )


@router.get("/facets")
async def facets():
    return await search_service.get_facets()
