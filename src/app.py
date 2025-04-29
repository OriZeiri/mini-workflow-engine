"""
FastAPI application for managing and running workflows with Redis-based storage.

Features:
- POST /workflow: Submit and run workflows with sequential or parallel steps
- GET /workflow_status/{run_id}: Query status of a workflow
- GET /runs: List all active runs (debug mode only)
"""

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
import asyncio
import uuid
from src.models import WorkflowRequest, StepType, TaskStatus, StepRuntime
import logging
from typing import List
import os
import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    - Connects to Redis on startup and stores the client in app.state.redis.
    - Closes Redis connection on shutdown.
    """
    rdb_client = await redis.from_url("redis://redis:6379", decode_responses=True)
    app.state.redis = rdb_client

    logger.info("Connected to Redis")
    pong = await rdb_client.ping()
    logger.info(f"Redis ping response: {pong}")

    yield
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

STEPS_KEY = "steps"

def task_a():
    """Dummy task A that logs execution and returns True."""
    logger.info("Running task A")
    return True

def task_b():
    """Dummy task B that logs execution and returns True."""
    logger.info("Running task B")
    return True

def task_c():
    """Dummy task C that logs execution and returns True."""
    logger.info("Running task C")
    return True

tasks_mapping = {
    "task_a": task_a,
    "task_b": task_b,
    "task_c": task_c
}

async def run_task(run_id: str,
                   all_steps: List[StepRuntime],
                   step: StepRuntime,
                   task_name: str,
                   rdb_conn):
    """
    Executes a single task in a workflow.

    - Updates the task status to 'running', 'success', or 'failed'.
    - Persists updated step state back to Redis.
    """
    logger.debug(f"Running task: {task_name} for run_id: {run_id}")

    task_func = tasks_mapping.get(task_name)
    if not task_func:
        logger.error(f"Task {task_name} not found in tasks_mapping")
        step.tasks[task_name] = TaskStatus.failed
    else:
        try:
            step.tasks[task_name] = TaskStatus.running
            await asyncio.to_thread(task_func)
            step.tasks[task_name] = TaskStatus.success
        except Exception as e:
            logger.error(f"Task {task_name} failed: {e}")
            step.tasks[task_name] = TaskStatus.failed

    await rdb_conn.hset(run_id, mapping={
        "steps": json.dumps([s.serialize() for s in all_steps])
    })
    logger.debug(f"Task {task_name} finished for run {run_id}")

def debug_only():
    """
    Dependency to restrict access to debug-only endpoints.

    Raises 403 Forbidden if DEBUG is not enabled.
    """
    if not DEBUG:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Debug mode is not enabled")

@app.get("/runs", dependencies=[Depends(debug_only)])
async def get_runs(request: Request):
    """
    Returns a list of all workflow run IDs stored in Redis.

    Requires DEBUG mode enabled.
    """
    rdb_client = request.app.state.redis
    keys = await rdb_client.keys("*")
    return {"run_ids": keys}

@app.post("/workflow")
async def run_workflow(request: Request, workflow: WorkflowRequest):
    """
    Starts a new workflow execution.

    - Accepts a list of steps (sequential/parallel) and tasks.
    - Stores initial state in Redis.
    - Launches background runner to process tasks.
    """
    run_id = str(uuid.uuid4())
    logger.debug(f"running run_id:{run_id}")

    runtime_steps = [
        StepRuntime(
            type=step.type,
            tasks={task: TaskStatus.pending for task in step.tasks},
            step_idx=idx
        )
        for idx, step in enumerate(workflow.steps)
    ]
    serialized_steps = [step.serialize() for step in runtime_steps]
    rdb = request.app.state.redis
    await rdb.hset(run_id, mapping={
        STEPS_KEY: json.dumps(serialized_steps)
    })

    logger.debug(f"steps: {runtime_steps}")

    async def runner(run_steps: List[StepRuntime], r_id: str, rdb_conn):
        """Runner coroutine that executes all steps for a workflow."""
        for step in run_steps:
            if step.type == StepType.parallel:
                await asyncio.gather(
                    *[run_task(r_id, run_steps, step, task, rdb_conn) for task in step.tasks]
                )
            elif step.type == StepType.sequential:
                for task in step.tasks:
                    await run_task(r_id, run_steps, step, task, rdb_conn)

    asyncio.create_task(runner(run_steps=runtime_steps, r_id=run_id, rdb_conn=rdb))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "run_id": run_id,
            "status_url": f"/workflow_status/{run_id}"
        },
    )

@app.get("/workflow_status/{run_id}")
async def workflow_status(run_id: str, request: Request):
    """
    Returns the current status of all steps for a given workflow run ID.

    - Retrieves and parses stored steps from Redis.
    - Raises 404 if the run ID is not found.
    """
    rdb_client = request.app.state.redis

    data = await rdb_client.hgetall(run_id)
    if not data:
        raise HTTPException(status_code=404, detail="Run ID not found")

    steps = json.loads(data["steps"])

    return {
        "run_id": run_id,
        "steps": steps,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
