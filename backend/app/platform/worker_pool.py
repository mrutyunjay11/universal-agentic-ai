from __future__ import annotations
import uuid
import time
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.platform.task_queue import task_queue, QueueItem, TaskStatus


class WorkerPoolType(str, Enum):
    GENERAL_WORKERS = "GENERAL_WORKERS"
    CODING_WORKERS = "CODING_WORKERS"
    BROWSER_WORKERS = "BROWSER_WORKERS"
    GPU_WORKERS = "GPU_WORKERS"
    RESEARCH_WORKERS = "RESEARCH_WORKERS"
    DATA_WORKERS = "DATA_WORKERS"
    SANDBOX_WORKERS = "SANDBOX_WORKERS"


class WorkerState(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    DRAINING = "DRAINING"
    DEAD = "DEAD"


class WorkerNode(BaseModel):
    worker_id: str = Field(default_factory=lambda: f"wrk_{uuid.uuid4().hex[:8]}")
    pool_type: WorkerPoolType = WorkerPoolType.GENERAL_WORKERS
    state: WorkerState = WorkerState.IDLE
    current_task_id: Optional[str] = None
    last_heartbeat: float = Field(default_factory=time.time)
    tasks_completed: int = 0
    tasks_failed: int = 0


class WorkerPool:
    """
    Manages pools of specialized worker nodes.
    Tracks worker health, heartbeats, dead worker reap, and lease re-queuing.
    """

    def __init__(self, heartbeat_timeout_seconds: float = 45.0):
        self.heartbeat_timeout = heartbeat_timeout_seconds
        self._workers: dict[str, WorkerNode] = {}

    def register_worker(self, pool_type: WorkerPoolType = WorkerPoolType.GENERAL_WORKERS) -> WorkerNode:
        worker = WorkerNode(pool_type=pool_type)
        self._workers[worker.worker_id] = worker
        return worker

    def heartbeat(self, worker_id: str) -> bool:
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        worker.last_heartbeat = time.time()
        if worker.state == WorkerState.DEAD:
            worker.state = WorkerState.IDLE
        return True

    def assign_task_to_worker(self, worker_id: str, task_id: str) -> bool:
        worker = self._workers.get(worker_id)
        if not worker or worker.state != WorkerState.IDLE:
            return False
        worker.state = WorkerState.BUSY
        worker.current_task_id = task_id
        return True

    def complete_worker_task(self, worker_id: str, success: bool = True) -> bool:
        worker = self._workers.get(worker_id)
        if not worker:
            return False
        worker.state = WorkerState.IDLE
        worker.current_task_id = None
        if success:
            worker.tasks_completed += 1
        else:
            worker.tasks_failed += 1
        return True

    def reap_dead_workers(self) -> list[str]:
        now = time.time()
        dead_workers = []
        for worker in self._workers.values():
            if now - worker.last_heartbeat > self.heartbeat_timeout:
                worker.state = WorkerState.DEAD
                dead_workers.append(worker.worker_id)
        return dead_workers

    def get_workers_by_pool(self, pool_type: WorkerPoolType) -> list[WorkerNode]:
        return [w for w in self._workers.values() if w.pool_type == pool_type and w.state != WorkerState.DEAD]

    def list_all_workers(self) -> list[WorkerNode]:
        return list(self._workers.values())


worker_pool = WorkerPool()
