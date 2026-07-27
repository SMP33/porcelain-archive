"""
Формирует PDF с текстом документа: текстовые блоки страниц (см.
porcelain_archive/pdf/parser.py и OCR-распознавание в text_from_image.py)
размещаются на странице по их позиции (rect, в процентах от размеров
страницы - общий формат для обоих источников текста), с учётом выравнивания
и размера шрифта - визуально похоже на оригинал, а не просто текст без вёрстки.
"""

import json
from pathlib import Path

import fitz
import pymupdf_fonts

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import get_commit_pages, log, log_progress

TEXT_FONT_NAME = "notos"  # Noto Sans (pymupdf_fonts) - поддерживает кириллицу.
TARGET_LONG_SIDE_PT = 841.9  # Страница нормализуется к этому масштабу (~A4).
DEFAULT_PAGE_SIZE_PT = (595.3, 841.9)  # A4 - для страниц без текста/размеров.
MIN_FONT_SIZE_PT = 6.0
MAX_FONT_SIZE_PT = 48.0
FONT_SHRINK_FACTOR = 0.85
MAX_FONT_SHRINK_ATTEMPTS = 6

ALIGN_MAP = {
    "left": fitz.TEXT_ALIGN_LEFT,
    "right": fitz.TEXT_ALIGN_RIGHT,
    "center": fitz.TEXT_ALIGN_CENTER,
    "justify": fitz.TEXT_ALIGN_JUSTIFY,
}


def page_size_and_scale(page_json):
    """
    Размер страницы в points и масштаб относительно исходных единиц: у
    страниц с текстом из PDF (porcelain_archive/pdf/parser.py) width/height
    уже в points, у страниц с OCR - в пикселях изображения. Приводим обе
    системы координат к единому масштабу по длинной стороне.
    """
    width = page_json.get("width")
    height = page_json.get("height")
    if not width or not height:
        return DEFAULT_PAGE_SIZE_PT, 1.0
    scale = TARGET_LONG_SIDE_PT / max(width, height)
    return (width * scale, height * scale), scale


def block_font_size(block, scale, page_h):
    """Размер шрифта блока: из font_size (PDF), либо оценка по высоте bbox (OCR)."""
    font_size = block.get("font_size")
    if font_size:
        return font_size * scale
    line_count = block.get("text", "").count("\n") + 1
    rect_height_pt = block["rect"]["height"] / 100 * page_h
    return max(MIN_FONT_SIZE_PT, min(MAX_FONT_SIZE_PT, rect_height_pt / line_count * 0.75))


def insert_text_fitted(pdf_page, rect, text, fontsize, align):
    """
    Вставляет текст в rect, уменьшая fontsize, пока он не поместится.
    insert_textbox при переполнении не рисует вообще ничего (не только
    "лишний" хвост) - без подгонки текст мог бы просто пропасть со страницы.
    """
    size = fontsize
    for _ in range(MAX_FONT_SHRINK_ATTEMPTS):
        if pdf_page.insert_textbox(rect, text, fontsize=size, fontname=TEXT_FONT_NAME, align=align) >= 0:
            return
        size *= FONT_SHRINK_FACTOR
        if size < MIN_FONT_SIZE_PT:
            break
    pdf_page.insert_textbox(rect, text, fontsize=MIN_FONT_SIZE_PT, fontname=TEXT_FONT_NAME, align=align)


info = TaskInfo.from_stdin()

document_id = info.data["document_id"]
commit = info.data["commit"]

pages = get_commit_pages(commit)

pdf_dir = Path(config.files.cache_path) / "download_text_pdf"
pdf_dir.mkdir(parents=True, exist_ok=True)
pdf_path = pdf_dir / f"{commit}.pdf"
tmp_pdf_path = pdf_dir / f"{commit}.pdf.tmp"

json_dir = Path(config.files.cache_path) / "json"

text_font = pymupdf_fonts.fitzfont(TEXT_FONT_NAME)

doc = fitz.open()
log(f"Сборка PDF из текста: {len(pages)} страниц(ы)")
for i, (pos, _image_hash, text_hash) in enumerate(pages, start=1):
    page_json = {}
    if text_hash is not None:
        text_path = json_dir / f"{text_hash}.json"
        if text_path.exists():
            try:
                page_json = json.loads(text_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                page_json = {}

    (page_w, page_h), scale = page_size_and_scale(page_json)
    pdf_page = doc.new_page(width=page_w, height=page_h)
    pdf_page.insert_font(fontname=TEXT_FONT_NAME, fontbuffer=text_font.buffer)

    for block in page_json.get("blocks", []):
        text = block.get("text", "").strip()
        if not text:
            continue
        rect_pct = block["rect"]
        rect = fitz.Rect(
            rect_pct["x"] / 100 * page_w,
            rect_pct["y"] / 100 * page_h,
            (rect_pct["x"] + rect_pct["width"]) / 100 * page_w,
            (rect_pct["y"] + rect_pct["height"]) / 100 * page_h,
        )
        insert_text_fitted(
            pdf_page,
            rect,
            text,
            fontsize=block_font_size(block, scale, page_h),
            align=ALIGN_MAP.get(block.get("alignment", "left"), fitz.TEXT_ALIGN_LEFT),
        )

    log_progress(i, len(pages), "Размещение текста")

doc.save(tmp_pdf_path)
doc.close()
tmp_pdf_path.replace(pdf_path)  # атомарно - читатели не должны увидеть недописанный PDF
log(f"PDF готов: {pdf_path}")
