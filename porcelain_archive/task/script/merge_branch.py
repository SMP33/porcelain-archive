from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import *

repo_path = None
document_id = None

try:
    info = TaskInfo.from_stdin()

    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]
    document_id = info.data["document_id"]

    repo_path = config.files.repos_root + f"/{document_id}"
    branch_path = config.files.repos_branch_root + f"/{branch_name}"

    try:
        run_git(branch_path, "merge", "--no-ff", "master", "-m", f"merge_master_into_{branch_name}")
    except Exception:
        run_git(branch_path, "merge", "--abort")
        raise

    run_git(repo_path, "merge", "--no-ff", branch_name, "-m", f"merge_{branch_name}")
    run_git(repo_path, "worktree", "remove", "--force", branch_path)

finally:
    if repo_path is not None:
        master_branch_id = get_master_branch_id(document_id)
        regenerate_branch_cache(repo_path, master_branch_id, None)
