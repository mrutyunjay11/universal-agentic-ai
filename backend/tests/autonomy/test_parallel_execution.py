import pytest
import asyncio
from app.autonomy.scheduler import AdvancedScheduler
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus


class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_concurrent_subtask_execution_safety(self):
        scheduler = AdvancedScheduler()
        graph = TaskGraph(master_task_id="m_par")

        for i in range(4):
            graph.add_subtask(SubTask(
                id=f"par_sub_{i}",
                title=f"Parallel Task {i}",
                objective=f"Execute step {i}",
                parent_task_id="m_par",
            ))

        executed_concurrently = []

        async def concurrent_executor(subtask: SubTask):
            executed_concurrently.append(subtask.id)
            await asyncio.sleep(0.01)
            subtask.status = SubTaskStatus.COMPLETED
            return {"id": subtask.id, "status": "COMPLETED"}

        results = await scheduler.schedule_and_execute(graph, concurrent_executor)

        assert len(results) == 4
        assert len(executed_concurrently) == 4
        assert graph.is_completed() is True
