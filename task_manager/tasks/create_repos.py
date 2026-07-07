import sys
import json

from task_manager.task_info import TaskInfo

print("inited")

info = TaskInfo.from_stdin()


print(json.dumps(info.model_dump_json(), indent=2))
