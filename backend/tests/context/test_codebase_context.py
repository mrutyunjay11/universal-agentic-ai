import pytest
from app.context.planner import ContextPlanner


class TestCodebaseContext:
    def test_codebase_task_requirement_decomposition(self):
        planner = ContextPlanner()
        plan = planner.create_context_plan("Refactor function process_payment in module payment.py")

        types = [req.requirement_type for req in plan.required_information]
        assert "CODE" in types
        assert "syntax_and_test_validation" in plan.verification_requirements
