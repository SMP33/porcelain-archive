import os
import shutil

from config import config
from .info import TaskInfo
from .task_utils import *

info = TaskInfo.from_stdin()

path = config.files.repos_root + f"/{info.data['document_id']}"
os.makedirs(path, exist_ok=True)
run_git(path, "init", "--initial-branch=master")

shutil.copytree(config.common.root + "/resource/repos", path, dirs_exist_ok=True)

run_git(path, "add", ".")
run_git(path, "lfs", "install", "--local")
run_git(path, "commit", "-m", "Инициализация")

regenerate_branch_cache(path, None, None)