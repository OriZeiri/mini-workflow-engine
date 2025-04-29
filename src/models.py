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

class StepInput(BaseModel):
    type: StepType
    tasks: List[str]

class StepRuntime(StepInput):
    tasks: Dict[str, TaskStatus]
    step_idx: Optional[int] = None

    def serialize(self) -> dict:
        return {
            "step_idx": self.step_idx,
            "type": self.type.value,
            "tasks": {task: status.value for task, status in self.tasks.items()}
        }
    @classmethod
    def deserialize(cls, data: dict) -> "StepRuntime":
        return cls(
            step_idx=data["step_idx"],
            type=StepType(data["type"]),
            tasks={task: TaskStatus(status) for task, status in data["tasks"].items()}
        )

class WorkflowRequest(BaseModel):
    steps: List[StepInput] = STEPS_DEBUG_VALUE