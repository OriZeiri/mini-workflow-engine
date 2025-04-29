# mini-workflow-engine
Workflow Engine Assignment - drivenets

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
