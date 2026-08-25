import pytest
from app.context.planner import ContextPlanner
from app.context.policies import ContextStrategy


class TestContextPlanner:
    def test_context_plan_generation_and_requirements(self):
        planner = ContextPlanner()

        plan = planner.create_context_plan(
            task="Determine whether library FastAPI supports Pydantic v2 migration"
        )

        assert plan.task.startswith("Determine")
        assert len(plan.required_information) >= 2
        assert "version_validation" in plan.verification_requirements
