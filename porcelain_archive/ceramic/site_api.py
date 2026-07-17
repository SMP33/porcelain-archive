from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from porcelain_archive.database import db

router = APIRouter(tags=["site"])


@router.get("/api/ceramic/site/stats")
async def stats():
    # page_count - заглушка (0): дешёвого агрегата по страницам всех документов нет
    # (страницы считаются per-branch через meta->>'page_count', см. document_service).
    rows = await db.execute_read("SELECT COUNT(*) FROM document WHERE is_visible = 1")
    doc_count = rows[0][0] if rows else 0
    return {"doc_count": doc_count, "page_count": 0}


@router.get("/robots.txt")
async def robots(request: Request):
    base = str(request.base_url).rstrip("/")
    body = (
        "User-agent: *\n"
        "Disallow: /ceramic/admin\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain")


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    base = str(request.base_url).rstrip("/") + "/ceramic"
    urls = [base + "/", base + "/search", base + "/about", base + "/feedback"]

    doc_rows = await db.execute_read("SELECT id FROM document WHERE is_visible = 1")
    for row in doc_rows:
        urls.append(f"{base}/document/{row[0]}")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")
    return Response(content="\n".join(lines), media_type="application/xml")
