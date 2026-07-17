from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from porcelain_archive.ceramic.document import document_service
from porcelain_archive.ceramic.factory import factory_service

router = APIRouter(tags=["site"])


@router.get("/api/ceramic/site/stats")
async def stats():
    data = await factory_service.stats()
    data["recent"] = await factory_service.list_recent(3)
    return data


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
    urls = [base + "/", base + "/objects", base + "/search", base + "/about", base + "/feedback"]

    factories = await factory_service.list_factories(0, 10_000)
    for f in factories["items"]:
        urls.append(f"{base}/object/{f['id']}")

    for doc_id in await document_service.sitemap_document_ids():
        urls.append(f"{base}/document/{doc_id}")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        lines.append(f"  <url><loc>{url}</loc></url>")
    lines.append("</urlset>")
    return Response(content="\n".join(lines), media_type="application/xml")
