from __future__ import annotations
import pytest
from app.agent.state import AgentState, PlanStep, StepStatus
from app.agent.executor import StepExecutionResult
from app.agent.observer import observation_manager
from app.agent.context import context_manager


class TestObserverAndContext:
    def test_observation_creation_and_evidence_extraction(self):
        state = AgentState(original_request="Test obs")
        step = PlanStep(id="s1", description="Search", objective="Search web")
        exec_res = StepExecutionResult(
            step_id="s1",
            tool_name="search_web",
            success=True,
            output={"results": [{"url": "https://example.com", "title": "Example", "snippet": "Useful snippet"}]},
        )
        obs = observation_manager.observe(step, exec_res, state)
        assert obs.success is True
        assert len(state.observations) == 1
        assert len(state.evidence) >= 1
        assert state.evidence[0]["title"] == "Example"

    def test_context_manager_slot_assembly(self):
        state = AgentState(original_request="Test context assembly", normalized_goal="Test context assembly")
        step = PlanStep(id="s1", description="Step 1", objective="Obj", status=StepStatus.COMPLETED)
        state.observations.append(observation_manager.observe(step, StepExecutionResult("s1", "calc", True, 42), state))

        sys_msg = context_manager.assemble_system_message(state)
        assert "Goal: Test context assembly" in sys_msg
        assert "Recent Observations:" in sys_msg
