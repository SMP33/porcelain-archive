"""
Формирует zip-архив исходных изображений документа (папка img/ ветки master)
для скачивания. Master - обычный (не sparse) checkout, поэтому файлы уже
лежат на диске в реальном виде и материализация из git не требуется.
"""

import zipfile
from pathlib import Path

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import log, log_progress, natural_sort_key

info = TaskInfo.from_stdin()

document_id = info.data["document_id"]
commit = info.data["commit"]

img_path = Path(config.files.repos_root) / str(document_id) / "img"

zip_dir = Path(config.files.cache_path) / "download_img_zip"
zip_dir.mkdir(parents=True, exist_ok=True)
zip_path = zip_dir / f"{commit}.zip"
tmp_zip_path = zip_dir / f"{commit}.zip.tmp"

files = sorted(
    (f for f in img_path.iterdir() if f.is_file() and f.name != ".gitkeep"),
    key=lambda f: natural_sort_key(f.name),
)
log(f"Формирование архива: {len(files)} файл(ов)")

with zipfile.ZipFile(tmp_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for i, file in enumerate(files, start=1):
        zf.write(file, file.name)
        log_progress(i, len(files), "Архивация файлов")

tmp_zip_path.replace(zip_path)  # атомарно - читатели не должны увидеть недописанный zip
log(f"Архив готов: {zip_path}")
