from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
import asyncio
import uuid
from models import WorkflowRequest, StepType, TaskStatus, StepRuntime
import logging
from typing import List

logger = logging.getLogger(__name__)
app = FastAPI()

# brute solution for now
runs = {}

def task_a():
    print("Running task A")
    return True

def task_b():
    print("Running task B")
    return True

def task_c():
    print("Running task C")
    return True

tasks_mapping = {
    "task_a": task_a,
    "task_b": task_b,
    "task_c": task_c
}

async def run_task(run_id: str, task_name: str):
    logger.debug(f"Running task: {task_name} for run_id: {run_id}")

@app.post("/workflow")
async def run_workflow(request: WorkflowRequest):
    run_id = str(uuid.uuid4())
    logger.debug(f"running run_id:{run_id}")

    runtime_steps = [
        StepRuntime(
            type=step.type,
            tasks={task: TaskStatus.pending for task in step.tasks},
            workflow_id=run_id,
            step_idx=idx
        )
        for idx, step in enumerate(request.steps)
    ]

    runs[run_id] = {"steps": runtime_steps}
    logger.debug(f"steps: {runtime_steps}")

    async def runner(steps_list: List[StepRuntime]):
       for step in steps_list:
            if step.type == StepType.parallel:
                await asyncio.gather(
                    *[run_task(run_id, task) for task in step.tasks]
                )
            elif step.type == StepType.sequential:
                for task in step.tasks:
                    await run_task(run_id, task)

    asyncio.create_task(runner(runtime_steps))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "run_id": run_id,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Run with: uvicorn main:app --reload