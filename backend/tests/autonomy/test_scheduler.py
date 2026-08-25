import pytest
from app.autonomy.scheduler import AdvancedScheduler
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus
from app.autonomy.policies import DelegationPolicy


class TestScheduler:
    @pytest.mark.asyncio
    async def test_parallel_batch_execution(self):
        scheduler = AdvancedScheduler(policy=DelegationPolicy(max_parallel_agents=3))
        graph = TaskGraph(master_task_id="m1")

        s1 = SubTask(id="s1", title="Task 1", objective="Do 1", parent_task_id="m1")
        s2 = SubTask(id="s2", title="Task 2", objective="Do 2", parent_task_id="m1")
        s3 = SubTask(id="s3", title="Task 3", objective="Do 3", parent_task_id="m1", dependencies=["s1", "s2"])

        graph.add_subtask(s1)
        graph.add_subtask(s2)
        graph.add_subtask(s3)

        execution_order = []

        async def mock_executor(subtask: SubTask):
            execution_order.append(subtask.id)
            subtask.status = SubTaskStatus.COMPLETED
            return {"subtask": subtask.id, "status": "COMPLETED"}

        results = await scheduler.schedule_and_execute(graph, mock_executor)

        assert len(results) == 3
        assert graph.is_completed() is True
        # s1 and s2 ran before s3
        assert execution_order.index("s3") > execution_order.index("s1")
        assert execution_order.index("s3") > execution_order.index("s2")
