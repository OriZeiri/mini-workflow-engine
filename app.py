from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
import asyncio
import uuid
from models import WorkflowRequest, StepType, TaskStatus, StepRuntime
import logging
from typing import List
import os

logger = logging.getLogger(__name__)
app = FastAPI()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
STEPS_KEY = "steps"

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

async def run_task(run_id: str, task_name: str, step_idx: int):
    logger.debug(f"Running task: {task_name} for run_id: {run_id}")
    if task_name not in tasks_mapping:
        logger.error(f"Task {task_name} not found!")
        runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.failed
        return  # just mark failed, don't throw

    task = tasks_mapping[task_name]

    try:
        runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.running
        result = await asyncio.to_thread(task)
        runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.success
        return result
    except Exception as e:
        runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.failed
        logger.error(f"Task {task_name} failed with error: {e}")

def debug_only():
    if not DEBUG:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Debug mode is not enabled")

@app.get("/runs", dependencies=[Depends(debug_only)])
async def get_runs():
    return runs

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

    runs[run_id] = {STEPS_KEY:runtime_steps}
    logger.debug(f"steps: {runtime_steps}")

    async def runner(steps_list: List[StepRuntime]):
       for step in steps_list:
            if step.type == StepType.parallel:
                await asyncio.gather(
                    *[run_task(run_id, task,step.step_idx) for task in step.tasks]
                )
            elif step.type == StepType.sequential:
                for task in step.tasks:
                    await run_task(run_id, task,step.step_idx)

    asyncio.create_task(runner(runtime_steps))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "run_id": run_id,
            "status_url": f"/workflow_status/{run_id}"
        },
    )

@app.get("/workflow_status/{run_id}")
async def workflow_status(run_id: str):
    if run_id not in runs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run ID not found")

    steps:List[StepRuntime] = runs[run_id]["steps"]
    serialized_steps = [
        {
            "step_idx": step.step_idx,
            "workflow_id": step.workflow_id,
            "type": step.type.value,
            "tasks": {task: task_status.value for task, task_status in step.tasks.items()}
        }
        for step in steps
    ]

    return {"run_id": run_id, "steps": serialized_steps}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Run with: uvicorn main:app --reload