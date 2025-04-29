import pytest
from app.models import StepRuntime, StepType, TaskStatus, WorkflowRequest,STEPS_DEBUG_VALUE

def test_step_runtime_serialize():
    """
    Test the serialization of a StepRuntime instance.

    Ensures that the `serialize` method correctly converts a StepRuntime
    object into a dictionary with the expected structure and values.
    """
    step = StepRuntime(
        type=StepType.parallel,
        step_idx=0,
        tasks={
            "task_a": TaskStatus.pending,
            "task_b": TaskStatus.running,
        }
    )

    serialized = step.serialize()

    assert serialized == {
        "step_idx": 0,
        "type": "parallel",
        "tasks": {
            "task_a": "pending",
            "task_b": "running"
        }
    }

def test_step_runtime_deserialize():
    """
    Test the deserialization of a StepRuntime instance.

    Ensures that the `deserialize` method correctly creates a StepRuntime
    object from a dictionary with the expected structure and values.
    """
    data = {
        "step_idx": 1,
        "type": "sequential",
        "tasks": {
            "task_x": "success",
            "task_y": "failed"
        }
    }

    step = StepRuntime.deserialize(data)

    assert isinstance(step, StepRuntime)
    assert step.step_idx == 1
    assert step.type == StepType.sequential
    assert isinstance(step.tasks, dict)
    assert step.tasks["task_x"] == TaskStatus.success
    assert step.tasks["task_y"] == TaskStatus.failed

def test_workflow_request_default_steps():
    """
    Test the default steps of a WorkflowRequest instance.

    Ensures that the `steps` attribute of a WorkflowRequest object
    initialized with `STEPS_DEBUG_VALUE` contains the expected default
    steps with correct types and tasks.
    """
    workflow = WorkflowRequest(steps=STEPS_DEBUG_VALUE)

    assert isinstance(workflow.steps, list)
    assert len(workflow.steps) == 2

    assert workflow.steps[0].type == StepType.parallel
    assert workflow.steps[0].tasks == ["task_a", "task_b"]

    assert workflow.steps[1].type == StepType.sequential
    assert workflow.steps[1].tasks == ["task_a", "task_b", "task_c"]

def test_invalid_step_type():
    """
    Test invalid step type in StepRuntime.

    Ensures that initializing a StepRuntime object with an invalid
    step type raises a ValueError.
    """
    with pytest.raises(ValueError):
        StepRuntime(
            type="invalid_type",  # should raise error
            step_idx=0,
            tasks={"task_a": TaskStatus.pending}
        )

def test_invalid_task_status():
    """
    Test invalid task status in StepRuntime deserialization.

    Ensures that deserializing a StepRuntime object with an invalid
    task status raises a ValueError.
    """
    bad_data = {
        "step_idx": 2,
        "type": "parallel",
        "tasks": {
            "task_invalid": "not_a_status"  # invalid status
        }
    }
    with pytest.raises(ValueError):
        StepRuntime.deserialize(bad_data)

def test_step_runtime_without_step_idx():
    """
    Test StepRuntime instance without a step index.

    Ensures that a StepRuntime object can be created without a `step_idx`
    and that the `serialize` method correctly handles this case.
    """
    step = StepRuntime(
        type=StepType.parallel,
        tasks={"task_a": TaskStatus.running}
    )

    assert step.step_idx is None
    serialized = step.serialize()
    assert serialized["step_idx"] is None

def test_round_trip_serialization():
    """
    Test round-trip serialization and deserialization of StepRuntime.

    Ensures that a StepRuntime object can be serialized and then
    deserialized back into an equivalent object with the same attributes.
    """
    original_step = StepRuntime(
        type=StepType.sequential,
        step_idx=5,
        tasks={
            "task1": TaskStatus.pending,
            "task2": TaskStatus.success
        }
    )

    serialized = original_step.serialize()
    restored_step = StepRuntime.deserialize(serialized)

    assert restored_step.step_idx == original_step.step_idx
    assert restored_step.type == original_step.type
    assert restored_step.tasks == original_step.tasks

def test_empty_workflow_request_steps():
    """
    Test WorkflowRequest with empty steps.

    Ensures that a WorkflowRequest object initialized with an empty
    list of steps has an empty `steps` attribute.
    """
    workflow = WorkflowRequest(steps=[])

    assert workflow.steps == []