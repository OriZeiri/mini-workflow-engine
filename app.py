from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
import asyncio
import uuid
from models import WorkflowRequest, StepType, TaskStatus, StepRuntime
import logging
from typing import List
import os

import redis.asyncio as redis
from contextlib import asynccontextmanager
import json

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    rdb_client = await redis.from_url("redis://localhost:6379", decode_responses=True)
    app.state.redis = rdb_client
    yield
    # Shutdown code
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

STEPS_KEY = "steps"

# brute solution for now
runs = {}

def task_a():
    logger.info("Running task A")
    return True

def task_b():
    logger.info("Running task B")
    return True

def task_c():
    logger.info("Running task C")
    return True

tasks_mapping = {
    "task_a": task_a,
    "task_b": task_b,
    "task_c": task_c
}

async def run_task(run_id: str, task_name: str, rdb_conn):
    logger.debug(f"Running task: {task_name} for run_id: {run_id}")
    # if task_name not in tasks_mapping:
    #     logger.error(f"Task {task_name} not found!")
    #     runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.failed
    #     return  # just mark failed, don't throw
    #
    # task = tasks_mapping[task_name]
    #
    # try:
    #     runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.running
    #     result = await asyncio.to_thread(task)
    #     runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.success
    #     logger.debug("Task completed successfully")
    #     return result
    # except Exception as e:
    #     runs[run_id]["steps"][step_idx].tasks[task_name] = TaskStatus.failed
    #     logger.error(f"Task {task_name} failed with error: {e}")

    # Fetch current workflow state
    data = await rdb_conn.hgetall(run_id)
    if not data:
        logger.error(f"Run ID {run_id} not found in Redis")
        return

    # Find the right step
    steps = [StepRuntime.deserialize(data=step) for step in json.loads(data[STEPS_KEY])]
    step = next((step for step in steps if task_name in step.tasks), None)
    logger.debug(f"step: {step}")
    if not step:
        logger.error(f"Task {task_name} not found in any step")
        return

    # Check if task function exists
    task_func = tasks_mapping.get(task_name)
    if not task_func:
        logger.error(f"Task {task_name} not found in tasks_mapping")
        step.tasks[task_name] = TaskStatus.failed

        await rdb_conn.hset(run_id, mapping={
            "steps": json.dumps([s.serialize() for s in steps]),
        })
        return

    # Run the task
    try:
        step.tasks[task_name] = TaskStatus.running
        await rdb_conn.hset(run_id, mapping={
            "steps": json.dumps([s.serialize() for s in steps]),
        })

        await asyncio.to_thread(task_func)
        step.tasks[task_name] = TaskStatus.success

    except Exception as e:
        logger.error(f"Task {task_name} failed with error: {e}")
        step.tasks[task_name] = TaskStatus.failed

    finally:
        # ALWAYS update Redis with final task status (success OR failed)
        await rdb_conn.hset(run_id, mapping={
            "steps": json.dumps([s.serialize() for s in steps]),
        })

        logger.debug(f"Task {task_name} finished for run {run_id}")

def debug_only():
    if not DEBUG:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Debug mode is not enabled")



@app.get("/runs", dependencies=[Depends(debug_only)])
async def get_runs(request: Request):
    rdb_client = request.app.state.redis

    keys = await rdb_client.keys("*")
    return {"run_ids": keys}


@app.post("/workflow")
async def run_workflow(request:Request, workflow: WorkflowRequest):
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
        STEPS_KEY:json.dumps(serialized_steps)
    })
    # runs[run_id] = {STEPS_KEY:runtime_steps}
    logger.debug(f"steps: {runtime_steps}")

    async def runner(steps_list: List[StepRuntime]):
       for step in steps_list:
            if step.type == StepType.parallel:
                logger.debug("running parallel steps")
                await asyncio.gather(
                    *[run_task(run_id, task, rdb) for task in step.tasks]
                )
            elif step.type == StepType.sequential:
                logger.debug("running sequential steps")
                for task in step.tasks:
                    await run_task(run_id, task, rdb)

    asyncio.create_task(runner(runtime_steps))

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "run_id": run_id,
            "status_url": f"/workflow_status/{run_id}"
        },
    )

@app.get("/workflow_status/{run_id}")
async def workflow_status(run_id: str, request: Request):
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

# Run with: uvicorn main:app --reload