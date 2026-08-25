import pytest
from app.agent.agent import universal_agent
from app.evaluation.evaluator import universal_evaluator
from app.tools.permissions import PermissionTier


class TestReproducibility:
    @pytest.mark.asyncio
    async def test_deterministic_task_reproducibility(self):
        # Deterministic math calculation should yield identical results across separate runs
        req = "Calculate (50 * 4) + sqrt(144)"

        state1 = universal_agent.create_task(req, permission_granted=PermissionTier.SYSTEM)
        res1 = await universal_agent.run_task(state1)

        state2 = universal_agent.create_task(req, permission_granted=PermissionTier.SYSTEM)
        res2 = await universal_agent.run_task(state2)

        assert res1.task_status == res2.task_status
        assert res1.final_result["summary"] == res2.final_result["summary"]

        eval1 = universal_evaluator.evaluate(res1)
        eval2 = universal_evaluator.evaluate(res2)

        assert eval1.overall_score == eval2.overall_score
        assert eval1.reproducibility >= 0.90
