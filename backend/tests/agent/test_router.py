from __future__ import annotations
import pytest
from app.agent.router import tool_router
from app.agent.executor import execution_engine
from app.agent.state import AgentState, PlanStep, StepStatus
from app.tools.permissions import PermissionTier


@pytest.mark.asyncio
class TestRouterAndExecutor:
    async def test_capability_routing(self):
        # file.read -> read_file
        t1 = tool_router.route_capability("file.read", PermissionTier.READ)
        assert t1 == "read_file"

        # math.calculate -> calculator
        t2 = tool_router.route_capability("math.calculate", PermissionTier.READ)
        assert t2 == "calculator"

        # verify.claims -> extract_claims
        t3 = tool_router.route_capability("verify.claims", PermissionTier.READ)
        assert t3 == "extract_claims"

    async def test_executor_safe_step_execution(self):
        state = AgentState(original_request="Math test", permission_granted=PermissionTier.READ)
        step = PlanStep(
            id="step_calc",
            description="Perform calculation",
            objective="Compute math",
            tool_name="calculator",
            tool_args={"expression": "100 / 4 + 25"},
        )
        res = await execution_engine.execute_step(step, state)
        assert res.success is True
        assert res.output["result"] == 50.0
        assert step.status == StepStatus.COMPLETED
        assert len(state.tool_calls) == 1
        assert len(state.tool_results) == 1
