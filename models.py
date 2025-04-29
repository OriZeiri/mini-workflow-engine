from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Union

STEPS_DEBUG_VALUE = [
    {"type": "parallel", "tasks": ["task_a", "task_b"]},
    {"type": "sequential", "tasks": ["task_a", "task_b","task_c"]}
  ]

class TaskStatus(Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"

class StepType(Enum):
    parallel = "parallel"
    sequential = "sequential"

class Step(BaseModel):
    type: StepType
    tasks: Union[List[TaskStatus],Dict[str, TaskStatus]]
    workflow_id: Optional[str] = None
    step_idx: Optional[int] = None

class WorkflowRequest(BaseModel):
    steps: List[Step] = STEPS_DEBUG_VALUE