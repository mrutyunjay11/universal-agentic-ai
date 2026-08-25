import pytest
from app.agent.agent import universal_agent
from app.evaluation.evaluator import universal_evaluator
from app.tools.permissions import PermissionTier


class TestEvaluationEndToEnd:
    @pytest.mark.asyncio
    async def test_full_pipeline_evaluation_and_reporting(self):
        # 1. Run realistic task
        state = universal_agent.create_task(
            request="Calculate (50 * 4) + sqrt(144)",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)

        # 2. Universal Evaluator evaluates complete trajectory
        eval_result = universal_evaluator.evaluate(completed)

        assert eval_result.task_id == completed.task_id
        assert eval_result.passed_gate is True
        assert eval_result.correctness >= 0.80
        assert eval_result.safety == 1.0
        assert len(eval_result.criteria_results) >= 1

        # 3. Generate Reports
        json_report = universal_evaluator.generate_report()
        assert "run_id" in json_report
        assert json_report["total_tasks"] >= 1
        assert json_report["pass_rate"] > 0.0

        md_report = universal_evaluator.generate_markdown_report()
        assert "# Evaluation Run Report" in md_report
        assert "Executive Summary" in md_report
