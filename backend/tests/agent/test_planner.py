from __future__ import annotations
import pytest
from app.agent.understanding import task_understander
from app.agent.planner import planner
from app.agent.plan_validator import plan_validator
from app.agent.state import TaskType, Plan, PlanStep, RiskLevel, VerificationRequirement
from app.tools.permissions import PermissionTier


class TestPlannerAndValidator:
    def test_dag_plan_generation_and_layering(self):
        und = task_understander.understand("Inspect the codebase, edit file, and verify code with unit tests")
        plan = planner.plan(und, TaskType.CODING)
        assert len(plan.steps) == 3

        # Topological sorting layers
        layers = planner.get_execution_layers(plan)
        assert len(layers) >= 2
        # First layer step_1 has no dependencies
        assert layers[0][0].id == "step_1"

    def test_plan_validator_acyclic_success(self):
        und = task_understander.understand("Calculate 100 * 25")
        plan = planner.plan(und, TaskType.MATHEMATICAL)
        val = plan_validator.validate(plan, permission_granted=PermissionTier.SYSTEM)
        assert val.valid is True
        assert len(val.errors) == 0

    def test_plan_validator_detects_cycle(self):
        # Create plan with artificial cycle
        step1 = PlanStep(id="s1", description="Step 1", objective="Obj 1", dependencies=["s2"])
        step2 = PlanStep(id="s2", description="Step 2", objective="Obj 2", dependencies=["s1"])
        plan = Plan(goal="Cycle test", steps=[step1, step2])

        val = plan_validator.validate(plan, permission_granted=PermissionTier.SYSTEM)
        assert val.valid is False
        assert any("Circular dependency" in err for err in val.errors)

    def test_plan_validator_permission_mismatch(self):
        # Step requires execute_terminal (EXECUTE permission) but only READ granted
        step = PlanStep(
            id="s1",
            description="Terminal command",
            objective="Run terminal",
            tool_name="execute_terminal",
            dependencies=[],
        )
        plan = Plan(goal="Perm test", steps=[step])
        val = plan_validator.validate(plan, permission_granted=PermissionTier.READ)
        assert val.valid is False
        assert any("requires tool 'execute_terminal' with permission" in err for err in val.errors)
