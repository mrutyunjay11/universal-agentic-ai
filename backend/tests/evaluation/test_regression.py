import pytest
from app.evaluation.regression import RegressionSuite
from app.agent.agent import universal_agent
from app.agent.state import AgentState, TaskState


class TestRegressionSuite:
    @pytest.mark.asyncio
    async def test_regression_case_lifecycle(self):
        suite = RegressionSuite()

        case = suite.add_case(
            title="Math calculation regression",
            original_failure_reason="Failed to evaluate addition with sqrt",
            request="Calculate (50 * 4) + sqrt(144)",
            expected_substrings=["212"],
        )

        assert case.id.startswith("reg_")
        assert len(suite.list_cases()) == 1

        passed, reason = await suite.run_case(case, universal_agent)
        assert passed is True
        assert case.last_run_passed is True

    @pytest.mark.asyncio
    async def test_create_case_from_failed_state(self):
        suite = RegressionSuite()
        failed_state = AgentState(
            original_request="Test broken feature",
            task_status=TaskState.FAILED,
        )

        case = suite.create_case_from_failed_state(failed_state, failure_reason="Missing tool dependency")
        assert "Test broken feature" in case.request
        assert case.original_failure_reason == "Missing tool dependency"
