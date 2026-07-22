import shutil
from pathlib import Path

from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import *

branch_path = None
branch_id = None
branch_name = None

try:
    info = TaskInfo.from_stdin()

    position = info.data["position"]
    tmpdir = Path(info.data["tmpdir"])

    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]
    branch_path = config.files.repos_branch_root + f"/{branch_name}"
    img_path = branch_path + "/img"
    doc_path = branch_path + "/doc"

    pdf_path = tmpdir / "source.pdf"
    if pdf_path.is_file():
        render_pdf_to_images(pdf_path, tmpdir, position)
        pdf_path.unlink()

    count = len([file for file in tmpdir.iterdir() if file.is_file()])

    shift_folder_files_up(branch_path, branch_name, "img", position, count)
    shift_folder_files_up(branch_path, branch_name, "doc", position, count)

    ADD_CHUNK_SIZE = 200  # ограничивает длину командной строки git add

    added_paths = []
    done = 0
    for file in tmpdir.iterdir():
        if file.is_file():
            validate_image(file)
            shutil.copy(file, img_path)
            json_path = Path(f"{doc_path}/{file.stem}.json")
            json_path.touch()
            added_paths.append(f"./img/{file.name}")
            added_paths.append(f"./doc/{file.stem}.json")
            done += 1
            log_progress(done, count, "Копирование файлов")

    added = 0
    for i in range(0, len(added_paths), ADD_CHUNK_SIZE * 2):
        chunk = added_paths[i:i + ADD_CHUNK_SIZE * 2]
        run_git(branch_path, "add", "--sparse", *chunk)
        added += len(chunk) // 2
        log_progress(added, count, "git add")

    run_git(branch_path, "commit", "-m", f"insert_{position}_{count}")

finally:
    shutil.rmtree(tmpdir)
    log(f"Удалена временная папка: {tmpdir}")

    remove_branch_trash(branch_path)
    regenerate_branch_cache(branch_path, branch_id, branch_name)
