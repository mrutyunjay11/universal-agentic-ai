from __future__ import annotations
import pytest
from app.agent.state import AgentState, Plan, PlanStep, StepStatus, FailureStrategy, VerificationRequirement
from app.agent.verifier import verification_coordinator
from app.agent.reflector import reflection_engine, ReflectionAction
from app.agent.replanner import replanner


@pytest.mark.asyncio
class TestVerifierReflectionReplanner:
    async def test_verification_math_claim(self):
        state = AgentState(original_request="Math verify")
        step = PlanStep(
            id="s1",
            description="Verify 12 * 12 == 144",
            objective="Confirm 144",
            tool_name="calculator",
            tool_args={"expression": "12 * 12"},
            result_summary="Computed 144.0",
            verification_required=VerificationRequirement.REQUIRED,
        )
        verdict = await verification_coordinator.verify_step(step, state)
        assert verdict is not None
        assert verdict.status == "verified"
        assert len(state.verification_results) == 1

    async def test_reflection_triggers_complete_when_all_steps_done(self):
        state = AgentState(original_request="Done test")
        step = PlanStep(id="s1", description="Done", objective="Done", status=StepStatus.COMPLETED)
        state.plan = Plan(goal="Done", steps=[step])
        refl = await reflection_engine.reflect(step, state)
        assert refl.action == ReflectionAction.COMPLETE

    async def test_replanner_inserts_retry_on_failure(self):
        failed_step = PlanStep(
            id="s1",
            description="Fail step",
            objective="Obj",
            status=StepStatus.FAILED,
            failure_strategy=FailureStrategy.RETRY,
            error="Connection timeout",
        )
        plan = Plan(goal="Replan test", steps=[failed_step])
        refl = await reflection_engine.reflect(failed_step, AgentState(original_request="Test"))
        assert refl.action == ReflectionAction.REPLAN

        new_plan = replanner.replan(plan, refl, failed_step)
        assert len(new_plan.steps) == 1
        assert new_plan.steps[0].id == "s1_retry"
        assert new_plan.steps[0].status == StepStatus.PENDING
