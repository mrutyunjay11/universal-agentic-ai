import pytest
from app.autonomy.orchestrator import MasterOrchestrator
from app.autonomy.policies import ExecutionMode


class TestMasterOrchestrator:
    @pytest.mark.asyncio
    async def test_single_agent_mode_execution(self):
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Calculate (50 * 4) + sqrt(144)",
            execution_mode=ExecutionMode.SINGLE_AGENT,
        )
        assert record.execution_mode == ExecutionMode.SINGLE_AGENT

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"
        assert "212" in str(completed.result)

    @pytest.mark.asyncio
    async def test_multi_agent_mode_execution(self):
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Research and verify Python 3.12 performance improvements across multiple sources",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )
        assert record.execution_mode == ExecutionMode.SPECIALIZED_MULTI_AGENT

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED", f"Graph: {completed.graph}, Result: {completed.result}"
        assert completed.result["completed_subtasks"] >= 2
        assert len(completed.result["artifacts"]) >= 1
