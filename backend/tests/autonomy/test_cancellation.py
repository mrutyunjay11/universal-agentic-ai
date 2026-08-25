import pytest
from app.autonomy.dispatcher import TaskDispatcher
from app.autonomy.task_graph import SubTask, SubTaskStatus


class TestCancellation:
    @pytest.mark.asyncio
    async def test_subtask_cancellation(self):
        dispatcher = TaskDispatcher()
        subtask = SubTask(
            id="sub_cancel_1",
            title="Long running subtask",
            objective="Perform extensive crawl",
            parent_task_id="m_cancel",
            status=SubTaskStatus.CANCELLED,
        )

        dispatcher.cancel_subtask("sub_cancel_1")
        result = await dispatcher.dispatch(subtask)

        assert "cancelled" in result.summary.lower()
