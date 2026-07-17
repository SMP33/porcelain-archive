"""
Рендер страниц документа (PDF → изображение) и распознавание текста (OCR).

extract_pages() — единственная публичная функция: принимает байты загруженного
файла (PDF или изображение) и возвращает список (jpeg-оригинал, jpeg-превью,
ocr_text) по одной записи на страницу. CPU-bound, вызывается через
asyncio.to_thread, чтобы не блокировать event loop.
"""
from __future__ import annotations

import io

try:
    import pytesseract as _tess
    _HAS_TESSERACT = True
except ImportError:
    _HAS_TESSERACT = False

try:
    import fitz as _fitz
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

from PIL import Image


def _pdf_to_pil(data: bytes) -> list[tuple]:
    """Return list of (PIL.Image, embedded_text) per page."""
    if not _HAS_FITZ:
        return []
    doc = _fitz.open(stream=data, filetype="pdf")
    results = []
    for page in doc:
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        text = page.get_text()
        results.append((img, text))
    return results


def ocr_image(img) -> str:
    if not _HAS_TESSERACT:
        return ""
    try:
        return _tess.image_to_string(img, lang="rus+eng")
    except Exception:
        return ""


def make_thumb(img, max_px: int = 400) -> bytes:
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px * 2))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def to_jpeg(img) -> bytes:
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    return buf.getvalue()


def extract_pages(data: bytes, ext: str, content_type: str) -> list[tuple[bytes, bytes, str]]:
    """CPU-bound: декодирование файла → список (jpeg-оригинал, jpeg-превью, OCR-текст)."""
    is_pdf = ext == ".pdf" or content_type == "application/pdf"
    out: list[tuple[bytes, bytes, str]] = []
    if is_pdf:
        for img, embedded_text in _pdf_to_pil(data):
            text = embedded_text.strip() or ocr_image(img)
            out.append((to_jpeg(img), make_thumb(img), text))
    else:
        try:
            img = Image.open(io.BytesIO(data))
        except Exception:
            return out
        out.append((to_jpeg(img), make_thumb(img), ocr_image(img)))
    return out
