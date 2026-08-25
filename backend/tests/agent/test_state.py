from __future__ import annotations
import pytest
from app.agent.state import (
    AgentState,
    TaskState,
    TaskType,
    Plan,
    PlanStep,
    StepStatus,
    VerificationVerdict,
    StructuredObservation,
    BudgetStatus,
)


class TestAgentState:
    def test_state_initialization(self):
        state = AgentState(original_request="Test task request")
        assert state.task_status == TaskState.PENDING
        assert state.task_type == TaskType.UNKNOWN
        assert state.iteration_count == 0
        assert not state.budget.is_exhausted

    def test_valid_state_transitions(self):
        state = AgentState(original_request="Valid transition test")
        assert state.transition_to(TaskState.UNDERSTANDING) is True
        assert state.transition_to(TaskState.PLANNING) is True
        assert state.transition_to(TaskState.PLAN_VALIDATION) is True
        assert state.transition_to(TaskState.EXECUTING) is True
        assert state.transition_to(TaskState.OBSERVING) is True
        assert state.transition_to(TaskState.VERIFYING) is True
        assert state.transition_to(TaskState.REFLECTING) is True
        assert state.transition_to(TaskState.COMPLETED) is True

    def test_invalid_state_transition_raises_error(self):
        state = AgentState(original_request="Invalid transition test")
        state.task_status = TaskState.COMPLETED
        # COMPLETED cannot jump straight to EXECUTING without reopening to PENDING
        with pytest.raises(ValueError, match="Invalid state transition"):
            state.transition_to(TaskState.EXECUTING)

    def test_state_serialization(self):
        state = AgentState(
            original_request="Serialize me",
            normalized_goal="Serialize me",
            task_type=TaskType.CODING,
        )
        state.observations.append(
            StructuredObservation(
                step_id="step_1",
                tool_name="list_directory",
                summary="Found 5 files",
                success=True,
            )
        )
        data = state.model_dump()
        assert data["original_request"] == "Serialize me"
        assert len(data["observations"]) == 1

        restored = AgentState(**data)
        assert restored.task_id == state.task_id
        assert restored.observations[0].tool_name == "list_directory"
