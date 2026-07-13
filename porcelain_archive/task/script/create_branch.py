from porcelain_archive.config import config
from porcelain_archive.task import TaskInfo
from porcelain_archive.task.utils import *

info = TaskInfo.from_stdin()

repo_path = config.files.repos_root + f"/{info.data['document_id']}"

branch_id = info.data['branch_id']
branch_name = info.data['branch_name']
branch_path = config.files.repos_branch_root + f"/{branch_name}"

run_git(repo_path,"worktree" ,"add", "--no-checkout", "-b", branch_name, branch_path)

run_git(branch_path, "sparse-checkout", "init", "--no-cone")
run_git(branch_path, "checkout", branch_name)
run_git(branch_path, "sparse-checkout", "add", "*/.gitkeep")

regenerate_branch_cache(repo_path, branch_id, branch_name)