import pytest
from app.context.planner import ContextPlanner
from app.context.evidence import RequirementCoverageReport
from app.context.sufficiency import ContextSufficiencyEvaluator
from app.context.policies import ContextSufficiencyStatus


class TestContextSufficiency:
    def test_sufficiency_evaluation_rules(self):
        planner = ContextPlanner()
        evaluator = ContextSufficiencyEvaluator()

        plan = planner.create_context_plan("Verify API compatibility")

        # 1. Complete coverage -> SUFFICIENT
        cov_complete = RequirementCoverageReport(
            total_requirements=2,
            covered_count=2,
            partial_count=0,
            missing_count=0,
            coverage_score=1.0,
            status="COMPLETE",
        )
        res_suff = evaluator.evaluate_sufficiency(plan, cov_complete)
        assert res_suff.status == ContextSufficiencyStatus.SUFFICIENT
        assert res_suff.is_sufficient is True

        # 2. Conflicted evidence -> CONFLICTED
        res_conf = evaluator.evaluate_sufficiency(plan, cov_complete, contradictions=["Contradictory claims found"])
        assert res_conf.status == ContextSufficiencyStatus.CONFLICTED
        assert res_conf.is_sufficient is False
