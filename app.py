from fastapi import FastAPI
import asyncio
import uuid

app = FastAPI()

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
    "task_a": task_a(),
    "task_b": task_b(),
    "task_c": task_c()
}

@app.post("/workflow")
async def run_workflow():
    # TODO: Implement workflow logic here
    return {"message": "Workflow received"}

# Run with: uvicorn main:app --reload