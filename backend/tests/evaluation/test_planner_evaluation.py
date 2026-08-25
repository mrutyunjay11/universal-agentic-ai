import pytest
from app.evaluation.planning_evaluator import PlannerEvaluator
from app.agent.state import Plan, PlanStep, VerificationRequirement


class TestPlannerEvaluator:
    def test_valid_acyclic_plan(self):
        evaluator = PlannerEvaluator()
        s1 = PlanStep(id="s1", description="Step 1", objective="Do 1", tool_name="search_web", verification_required=VerificationRequirement.REQUIRED)
        s2 = PlanStep(id="s2", description="Step 2", objective="Do 2", tool_name="calculator", dependencies=["s1"])
        plan = Plan(plan_id="p1", goal="Valid Goal", steps=[s1, s2])

        res = evaluator.evaluate_plan(plan)
        assert res["is_acyclic"] is True
        assert res["has_redundant_steps"] is False
        assert res["score"] >= 0.85
        assert len(res["issues"]) == 0

    def test_cyclic_plan_detection(self):
        evaluator = PlannerEvaluator()
        s1 = PlanStep(id="s1", description="Step 1", objective="Do 1", tool_name="search_web", dependencies=["s2"])
        s2 = PlanStep(id="s2", description="Step 2", objective="Do 2", tool_name="calculator", dependencies=["s1"])
        plan = Plan(plan_id="p1", goal="Cyclic Goal", steps=[s1, s2])

        res = evaluator.evaluate_plan(plan)
        assert res["is_acyclic"] is False
        assert res["score"] < 0.60
        assert any("circular" in i.lower() for i in res["issues"])
