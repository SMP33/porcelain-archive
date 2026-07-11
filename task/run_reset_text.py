import json
from pathlib import Path

from config import config
from .info import TaskInfo
from .task_utils import *

branch_path = None
branch_id = None
branch_name = None

try:
    info = TaskInfo.from_stdin()

    start = info.data["start"]
    end = info.data["end"]

    branch_id = info.data["branch_id"]
    branch_name = info.data["branch_name"]
    branch_path = config.files.repos_branch_root + f"/{branch_name}"
    doc_path = branch_path + "/doc"

    for pos in range(start, end + 1):
        json_path = Path(f"{doc_path}/{pos}.json")
        json_path.write_text(json.dumps({}), encoding="utf-8")
        run_git(branch_path, "add", "--sparse", f"./doc/{pos}.json")

    run_git(branch_path, "commit", "-m", f"reset_text_{start}_{end}")

finally:
    remove_branch_trash(branch_path)
    regenerate_branch_cache(branch_path, branch_id, branch_name)
