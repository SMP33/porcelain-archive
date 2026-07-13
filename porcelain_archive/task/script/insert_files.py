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

    count = len([file for file in tmpdir.iterdir() if file.is_file()])

    shift_folder_files_up(branch_path, branch_name, "img", position, count)
    shift_folder_files_up(branch_path, branch_name, "doc", position, count)

    for file in tmpdir.iterdir():
        if file.is_file():
            validate_image(file)
            shutil.copy(file, img_path)
            json_path=Path(f"{doc_path}/{file.stem}.json")
            json_path.touch()
            run_git(branch_path, "add", "--sparse", f"./img/{file.name}", f"./doc/{file.stem}.json")

    run_git(branch_path, "commit", "-m", f"insert_{position}_{count}")

finally:
    shutil.rmtree(tmpdir)
    log(f"Удалена временная папка: {tmpdir}")

    remove_branch_trash(branch_path)
    regenerate_branch_cache(branch_path, branch_id, branch_name)
