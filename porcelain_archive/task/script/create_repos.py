import os
import shutil

from ...config.config import config
from ..info import TaskInfo
from ..utils import *

info = TaskInfo.from_stdin()

document_id = info.data['document_id']
path = config.files.repos_root + f"/{document_id}"
os.makedirs(path, exist_ok=True)
run_git(path, "init", "--initial-branch=master")

shutil.copytree(config.common.root + "/porcelain_archive/task/resource/initial_repos", path, dirs_exist_ok=True)

run_git(path, "add", ".")
run_git(path, "lfs", "install", "--local")
run_git(path, "commit", "-m", "Инициализация")

master_branch_id = get_master_branch_id(document_id)
regenerate_branch_cache(path, master_branch_id, None)