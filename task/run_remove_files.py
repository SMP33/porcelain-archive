from config import config
from .info import TaskInfo
from .task_utils import *

branch_path = None
branch_id = None
branch_name = None

try:
    info = TaskInfo.from_stdin()

    position = info.data["position"]
    file_remove_count = info.data["file_remove_count"]

    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]
    branch_path = config.files.repos_branch_root + f"/{branch_name}"

    remove_from = position
    remove_to = position + file_remove_count - 1

    remove_and_shift_folder_files(
        branch_path, branch_name, "img", remove_from, remove_to, file_remove_count
    )
    remove_and_shift_folder_files(
        branch_path, branch_name, "doc", remove_from, remove_to, file_remove_count
    )

    run_git(branch_path, "commit", "-m", f"remove_{position}_{file_remove_count}")

finally:
    remove_branch_trash(branch_path)
    regenerate_branch_cache(branch_path, branch_id, branch_name)
