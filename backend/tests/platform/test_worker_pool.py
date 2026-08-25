import pytest
import time
from app.platform.worker_pool import WorkerPool, WorkerPoolType, WorkerState


class TestWorkerPool:
    def test_worker_registration_and_task_lifecycle(self):
        pool = WorkerPool()
        worker = pool.register_worker(WorkerPoolType.CODING_WORKERS)

        assert worker.pool_type == WorkerPoolType.CODING_WORKERS
        assert worker.state == WorkerState.IDLE

        # Assign task
        assigned = pool.assign_task_to_worker(worker.worker_id, "task_coding_01")
        assert assigned is True
        assert worker.state == WorkerState.BUSY

        # Complete task
        pool.complete_worker_task(worker.worker_id, success=True)
        assert worker.state == WorkerState.IDLE
        assert worker.tasks_completed == 1

    def test_dead_worker_reaping(self):
        pool = WorkerPool(heartbeat_timeout_seconds=0.1)
        worker = pool.register_worker(WorkerPoolType.GENERAL_WORKERS)

        time.sleep(0.15)
        dead = pool.reap_dead_workers()
        assert worker.worker_id in dead
        assert worker.state == WorkerState.DEAD
