from __future__ import annotations

from fastapi import APIRouter, Query

from .search_service import PER_PAGE_DEFAULT, search_service

router = APIRouter(prefix="/api/ceramic/search", tags=["search"])


@router.get("")
@router.get("/")
async def search(
    q: str = "",
    year_from: int = Query(0, ge=0),
    year_to: int = Query(0, ge=0),
    pointer: list[str] = Query(default=[]),
    pages_from: int = Query(0, ge=0),
    pages_to: int = Query(0, ge=0),
    offset: int = 0,
    limit: int = PER_PAGE_DEFAULT,
):
    return await search_service.search(
        q, year_from, year_to, offset, limit, pointer, pages_from, pages_to
    )


@router.get("/facets")
async def facets():
    return await search_service.get_facets()
