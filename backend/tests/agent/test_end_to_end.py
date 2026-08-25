from __future__ import annotations
import os
import shutil
import tempfile
import pytest
from app.agent.agent import universal_agent
from app.agent.state import TaskState, TaskType
from app.tools.permissions import PermissionTier


@pytest.fixture
def temp_project_dir():
    d = tempfile.mkdtemp(prefix="test_agent_e2e_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.asyncio
class TestAgentEndToEndScenarios:
    async def test_scenario_a_research_pipeline(self):
        # Scenario A: Research goal -> Search -> Evidence -> Verification -> Completion
        state = universal_agent.create_task(
            request="Search documentation for Python asyncio subprocess features and verify citations",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)
        assert completed.task_status == TaskState.COMPLETED
        assert completed.task_type in (TaskType.RESEARCH, TaskType.MULTI_DOMAIN)
        assert completed.final_result is not None
        assert completed.confidence >= 0.70
        assert len(completed.tool_calls) >= 1

    async def test_scenario_b_coding_pipeline(self, temp_project_dir):
        # Scenario B: Coding task -> List files -> Verify code -> Complete
        universal_agent.project_root = temp_project_dir
        state = universal_agent.create_task(
            request="Inspect project and implement an addition function in python with unit test verification",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)
        assert completed.task_status == TaskState.COMPLETED
        assert completed.task_type in (TaskType.CODING, TaskType.MULTI_DOMAIN)
        assert len(completed.verification_results) >= 1

    async def test_scenario_c_fact_verification(self):
        # Scenario C: Fact checking -> Evidence lookup -> Cross-examination -> Verdict
        state = universal_agent.create_task(
            request="Fact-check whether Python 3.12 has subinterpreters support in official documentation",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)
        assert completed.task_status == TaskState.COMPLETED
        assert completed.final_result is not None

    async def test_scenario_d_data_analysis(self, temp_project_dir):
        # Scenario D: Data analysis task -> CSV dataset inspection & stats
        universal_agent.project_root = temp_project_dir
        # Prepare sample csv
        csv_path = os.path.join(temp_project_dir, "data.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("id,score,age\n1,95,25\n2,88,30\n3,92,28\n")

        state = universal_agent.create_task(
            request="Read data.csv and calculate statistics on the dataset",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)
        assert completed.task_status == TaskState.COMPLETED

    async def test_scenario_e_mathematical_calculation(self):
        # Scenario E: Math -> AST safe calculator -> Verification
        state = universal_agent.create_task(
            request="Calculate (50 * 4) + sqrt(144)",
            permission_granted=PermissionTier.SYSTEM,
        )
        completed = await universal_agent.run_task(state)
        assert completed.task_status == TaskState.COMPLETED
        assert any(obs.tool_name == "calculator" for obs in completed.observations)
        assert any(v.status == "verified" for v in completed.verification_results)

    async def test_task_cancellation(self):
        state = universal_agent.create_task(request="Long task to cancel")
        cancelled = await universal_agent.cancel_task(state.task_id)
        assert cancelled.task_status == TaskState.CANCELLED
