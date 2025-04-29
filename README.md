# mini-workflow-engine
Workflow Engine Assignment - drivenets.

checkout my submission [here](#mini-workflow-engine--submission-summary)

### Objective

Implement a **mini workflow engine** in Python using **FastAPI**. Your engine should be able to run specific tasks—either **in parallel** or **in sequence**—based on requests sent to a **single endpoint**.

---

## Core Tasks

You have three simple tasks:

```python
from fastapi import FastAPI

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

@app.post("/workflow")
async def run_workflow():
    # TODO: Implement workflow logic here
    return {"message": "Workflow received"}

# Run with: uvicorn main:app --reload
```

- Each task **must return** either `True` (for success) or `False` (for failure).
- You are free to change the function bodies or add more tasks as needed.

---

## Requirements

1. **Single Endpoint**
    - Expose **one** FastAPI endpoint that receives a request describing how the tasks should run:
        - **In parallel** (e.g., task A and task B can run simultaneously).
        - **In sequence** (e.g., task A → task B → task C in a specific order).
        - A **mix** of parallel and sequential steps (e.g., parallel tasks, then a final sequential task).
2. **Flow Definition**
    - You decide **how** the user specifies which tasks to run and in what order.
    - You can think of it as a small “DAG” definition or any custom structure you prefer.
3. **Run Tracking**
    - Each workflow execution should have a **unique run ID** (e.g., a UUID).
    - Keep track of each task’s **status** (e.g., pending, running, succeeded, failed).
    - Decide where to store this information. The environment provides a **Redis** instance if you want to use it.
    - The design should allow multiple pods (containers) to handle requests in a **stateless** manner.

---

---

## Testing

- **Test your solution** using any framework you prefer (e.g., `pytest`) or your own method.
    - Show how you would handle external dependencies (mocking, monkey patching, or similar) if any tasks require external call

---

## Notes

- You have **Redis** available, but you are **not** required to use it unless you find it helpful.
- Your design decisions—request format, storage mechanism, concurrency model—are up to you.
- Demonstrate clarity of thought, concise code, and an appropriate level of robustness for a workflow engine.

---

**Good luck!** This exercise is open-ended. Focus on making your solution **functional**, **clear**, and **extensible**. Feel free to include any documentation or diagrams that help explain your design choices.

---
# Mini Workflow Engine – Submission Summary

## 📌 Overview

This project is a mini workflow engine built with FastAPI that can execute tasks either in parallel or in sequence, based on the client’s request. 

It uses Redis to track workflow state and task progress, enabling stateless operation across multiple containers.

---

## ⚙️ How It Works

- A single endpoint `POST /workflow` accepts a workflow definition.
- The definition contains a list of steps.
- Each step can be:
  - **Sequential**: tasks run one after the other.
  - **Parallel**: tasks run simultaneously using `asyncio.gather`.
- The server:
  - Assigns a unique `run_id` using `uuid4()`.
  - Stores all task states in Redis under that `run_id`.
  - Launches background processing for each task.
- Clients can:
  - Check status via `GET /workflow_status/{run_id}`
  - List all runs via `GET /runs` (enabled only if `DEBUG=true`)

---

## 🔄 Example DAG (Simplified)

The "DAG" is modeled as a **list of steps**. Each step is a dictionary with:
- a `"type"` field: either `"sequential"` or `"parallel"`
- a `"tasks"` field: list of task names to run

### Example:
```json
{
  "steps": [
    { "type": "parallel", "tasks": ["task_a", "task_b"] },
    { "type": "sequential", "tasks": ["task_c"] }
  ]
}
```
➡ This runs task_a and task_b together, then runs task_c after both finish.

---
## 📦 Design Choices
- Request Format: Easy-to-read JSON with step type and task list.
- Redis: Used to persist workflow steps and their status.
- Stateless: The app reads from Redis each time — making it suitable for distributed or containerized environments.
- Concurrency:
  - Sequential tasks are awaited in order.
  - Parallel tasks are launched with `asyncio.gather`.

- Task Execution: Each task runs via `asyncio.to_thread(...)`, allowing real functions to be offloaded safely.
---
## ✅ Testing
- Tests are written using `pytest` and cover:

- `POST /workflow` – workflow is saved and launched
- `run_task()` – success and failure behavior
- `GET /workflow_status/{run_id}` – returns status from Redis
- `GET /runs` – works only in DEBUG mode
- All Redis interactions are mocked

- Model testing
  - The StepRuntime and WorkflowRequest classes are fully tested for:
  - Serialization and deserialization
  - Valid and invalid data
  - Round-trip conversion (object → JSON → object)
  - Empty and default workflow structures

run the tests with:
```bash
pytest -v
```


---
## ▶️ How to Run
1. Make sure Docker and Docker Compose are installed.

2. Run the project with:

```bash
docker-compose up --build
```
The API will be available at:
📍 http://localhost:8000

📘 Swagger docs: http://localhost:8000/docs
## 💬 Personal Note
This was a really fun project to implement — simple but full of interesting decisions around task orchestration, concurrency, and system design.

If I were to build this again, I’d experiment with modeling the workflow as a graph structure (DAG) instead of a flat list of steps. This would allow more flexible branching and dependencies between tasks, like real-world orchestration systems.

Thanks for the challenge!

---