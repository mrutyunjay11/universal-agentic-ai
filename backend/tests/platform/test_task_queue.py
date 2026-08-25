import pytest
from app.platform.task_queue import DurableTaskQueue, TaskPriority, TaskStatus


class TestTaskQueue:
    def test_priority_dispatching(self):
        queue = DurableTaskQueue()
        queue.enqueue("task_low", {}, priority=TaskPriority.LOW)
        queue.enqueue("task_crit", {}, priority=TaskPriority.CRITICAL)
        queue.enqueue("task_norm", {}, priority=TaskPriority.NORMAL)

        # 1st leased must be CRITICAL
        first = queue.lease_next_task("worker-1")
        assert first is not None
        assert first.task_id == "task_crit"
        assert first.status == TaskStatus.LEASED

        # 2nd leased must be NORMAL
        second = queue.lease_next_task("worker-2")
        assert second is not None
        assert second.task_id == "task_norm"

    def test_dead_letter_requeue_on_max_retries(self):
        queue = DurableTaskQueue()
        item = queue.enqueue("task_faulty", {}, priority=TaskPriority.NORMAL)

        # Fail 3 times
        queue.fail_and_requeue(item.id, "worker-1", "DB Connection Failed")
        queue.fail_and_requeue(item.id, "worker-1", "DB Connection Failed")
        queue.fail_and_requeue(item.id, "worker-1", "DB Connection Failed")

        dlq = queue.get_dead_letter_items()
        assert len(dlq) == 1
        assert dlq[0].task_id == "task_faulty"
        assert dlq[0].status == TaskStatus.DEAD_LETTER
