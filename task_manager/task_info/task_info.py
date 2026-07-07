from typing import Optional
import json
import sys
from pydantic import BaseModel

class TaskInfo(BaseModel):
    id: int
    type: str
    repos_path: Optional[str] = None
    data: Optional[dict] = None
    
    @staticmethod
    def from_stdin() -> "TaskInfo":
        return TaskInfo(**json.load(sys.stdin))