from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile

from porcelain_archive.ceramic.user import require_role

from .document_service import document_service

router = APIRouter(prefix="/api/ceramic/documents", tags=["documents"])

_FORM_FIELDS = (
    "factory_id", "title", "doc_type", "doc_date", "description", "author",
    "source_archive", "fund", "inventory_no", "case_no", "sheets",
    "authenticity", "language", "keywords", "geography",
)


@router.get("")
@router.get("/")
async def list_documents(factory_id: int = 0, offset: int = 0, limit: int = 30):
    return await document_service.list_documents(factory_id or None, offset, limit)


@router.get("/admin")
async def admin_list_documents(
    q: str = "",
    factory_id: int = 0,
    issues: str = "",
    offset: int = 0,
    limit: int = 50,
    _: dict = Depends(require_role("admin")),
):
    return await document_service.admin_list(q, factory_id, issues, offset, limit)


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def create_document(request: Request, _: dict = Depends(require_role("contributor"))):
    body = await request.json()
    fields = {k: body.get(k) for k in _FORM_FIELDS}
    if not fields.get("title") or not str(fields["title"]).strip():
        raise HTTPException(status_code=400, detail="Укажите название документа")
    document_id = await document_service.create_document(fields)
    return {"id": document_id}


@router.get("/{document_id}")
async def get_document(document_id: int):
    doc = await document_service.get_document(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return doc


@router.put("/{document_id}")
async def update_document(document_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    fields = {k: body.get(k) for k in _FORM_FIELDS}
    await document_service.update_document(document_id, fields)
    return {"ok": True}


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, _: dict = Depends(require_role("admin"))):
    await document_service.delete_document(document_id)


@router.get("/{document_id}/pages")
async def list_pages(document_id: int, _: dict = Depends(require_role("admin"))):
    return await document_service.list_pages(document_id)


@router.post("/{document_id}/pages")
async def upload_pages(document_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    form = await request.form()
    files = [f for f in form.getlist("files") if isinstance(f, UploadFile)]
    try:
        return await document_service.upload_pages(document_id, files)
    except ValueError:
        raise HTTPException(status_code=404, detail="Документ не найден")


@router.delete("/{document_id}/pages/{page_number}", status_code=204)
async def delete_page(document_id: int, page_number: int, _: dict = Depends(require_role("admin"))):
    await document_service.delete_page(document_id, page_number)


@router.put("/{document_id}/pages/text")
async def update_pages_text(document_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    pages = body.get("pages", {})
    try:
        await document_service.update_pages_text(document_id, pages)
    except ValueError:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return {"ok": True}


@router.put("/{document_id}/pages/order")
async def reorder_pages(document_id: int, request: Request, _: dict = Depends(require_role("admin"))):
    body = await request.json()
    order = body.get("order", [])
    await document_service.reorder_pages(document_id, order)
    return {"ok": True}
