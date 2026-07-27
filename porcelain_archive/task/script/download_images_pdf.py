"""
Формирует PDF из кешированных (web-качество) изображений страниц документа
для скачивания.
"""

from pathlib import Path

from PIL import Image

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import get_commit_pages, log, log_progress

info = TaskInfo.from_stdin()

document_id = info.data["document_id"]
commit = info.data["commit"]

pages = get_commit_pages(commit)

pdf_dir = Path(config.files.cache_path) / "download_images_pdf"
pdf_dir.mkdir(parents=True, exist_ok=True)
pdf_path = pdf_dir / f"{commit}.pdf"
tmp_pdf_path = pdf_dir / f"{commit}.pdf.tmp"

web_dir = Path(config.files.cache_path) / "web"

images = []
log(f"Сборка PDF из изображений: {len(pages)} страниц(ы)")
for i, (pos, image_hash, _text_hash) in enumerate(pages, start=1):
    if image_hash is not None:
        image_path = web_dir / f"{image_hash}.jpg"
        if image_path.exists():
            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            images.append(image)
    log_progress(i, len(pages), "Обработка изображений")

if not images:
    raise ValueError(f"У документа {document_id} нет ни одной страницы с изображением")

images[0].save(tmp_pdf_path, "PDF", save_all=True, append_images=images[1:])
tmp_pdf_path.replace(pdf_path)  # атомарно - читатели не должны увидеть недописанный PDF
log(f"PDF готов: {pdf_path}")
