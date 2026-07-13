import json
import shutil
from pathlib import Path

from porcelain_archive.pdf import parser as extract_pdf_blocks

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import *

branch_path = None
branch_id = None
branch_name = None
tmpdir = None

try:
    info = TaskInfo.from_stdin()

    position = info.data["position"]
    pdf_path = info.data["pdf_path"]
    tmpdir = str(Path(pdf_path).parent)

    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]
    branch_path = config.files.repos_branch_root + f"/{branch_name}"
    doc_path = branch_path + "/doc"

    page_count = len(list_position_files(branch_path, branch_name, "img"))

    pages = extract_pdf_blocks.extract_sequence(pdf_path)
    if position + len(pages) - 1 > page_count:
        raise ValueError(
            f"PDF содержит {len(pages)} страниц(ы), начиная с позиции {position} "
            f"это выходит за пределы версии документа ({page_count} страниц)"
        )

    for offset, page in enumerate(pages):
        target_pos = position + offset
        json_path = Path(f"{doc_path}/{target_pos}.json")
        json_path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
        run_git(branch_path, "add", "--sparse", f"./doc/{target_pos}.json")

    run_git(branch_path, "commit", "-m", f"set_text_{position}_{len(pages)}")

finally:
    if tmpdir is not None:
        shutil.rmtree(tmpdir, ignore_errors=True)
        log(f"Удалена временная папка: {tmpdir}")

    if branch_path is not None:
        remove_branch_trash(branch_path)
        regenerate_branch_cache(branch_path, branch_id, branch_name)
