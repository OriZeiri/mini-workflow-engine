import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.app import app, run_task
from src.models import StepRuntime, StepType, TaskStatus


@pytest.fixture
def mock_redis():
    """Patch Redis client used in app.state.redis for isolated unit tests."""
    with patch("src.app.redis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_instance = AsyncMock()
        mock_from_url.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_post_workflow_success(mock_redis):
    """Test POST /workflow returns 200 and saves steps to Redis."""
    app.state.redis = mock_redis
    steps = [{"type": "sequential", "tasks": ["task_a", "task_b"]}]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/workflow", json={"steps": steps})

    assert resp.status_code == 200
    body = resp.json()
    assert "run_id" in body
    assert "status_url" in body
    mock_redis.hset.assert_called_once()


@pytest.mark.asyncio
async def test_run_task_success_updates_status():
    """Test that run_task() marks task as success and calls Redis hset."""
    step = StepRuntime(type=StepType.sequential, tasks={"task_a": TaskStatus.pending}, step_idx=0)
    steps = [step]
    mock_redis = AsyncMock()

    await run_task("test_run", steps, step, "task_a", mock_redis)

    assert step.tasks["task_a"] == TaskStatus.success
    mock_redis.hset.assert_called_once()


@pytest.mark.asyncio
async def test_run_task_unknown_sets_failed():
    """Test that run_task() handles unknown tasks and sets status to failed."""
    step = StepRuntime(type=StepType.sequential, tasks={"does_not_exist": TaskStatus.pending}, step_idx=0)
    steps = [step]
    mock_redis = AsyncMock()

    await run_task("test_run", steps, step, "does_not_exist", mock_redis)

    assert step.tasks["does_not_exist"] == TaskStatus.failed
    mock_redis.hset.assert_called_once()


@pytest.mark.asyncio
async def test_get_workflow_status_success(mock_redis):
    """Test GET /workflow_status/{run_id} returns correct step data from Redis."""
    app.state.redis = mock_redis
    run_id = "test_run_id"

    mock_redis.hgetall.return_value = {
        "steps": json.dumps([
            {"type": "sequential", "tasks": {"task_a": "pending"}, "step_idx": 0}
        ])
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/workflow_status/{run_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == run_id
    assert isinstance(body["steps"], list)
    assert body["steps"][0]["tasks"]["task_a"] == "pending"


@pytest.mark.asyncio
async def test_get_runs_debug_true(mock_redis):
    """Test GET /runs returns list of run_ids if DEBUG=True."""
    app.state.redis = mock_redis
    from src import app as app_module
    app_module.DEBUG = True

    mock_redis.keys.return_value = ["run1", "run2"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/runs")

    assert resp.status_code == 200
    data = resp.json()
    assert set(data["run_ids"]) == {"run1", "run2"}


@pytest.mark.asyncio
async def test_get_runs_debug_false(mock_redis):
    """Test GET /runs returns 403 Forbidden if DEBUG=False."""
    app.state.redis = mock_redis
    from src import app as app_module
    app_module.DEBUG = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/runs")

    assert resp.status_code == 403
