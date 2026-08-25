from __future__ import annotations
import uuid
import time
import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    LEASED = "LEASED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DEAD_LETTER = "DEAD_LETTER"


class QueueItem(BaseModel):
    id: str = Field(default_factory=lambda: f"qitem_{uuid.uuid4().hex[:8]}")
    task_id: str
    pool_type: str = "GENERAL_WORKERS"
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    lease_owner: Optional[str] = None
    lease_expires_at: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    delayed_until: float = 0.0
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


class DurableTaskQueue:
    """
    Durable, provider-agnostic priority task queue.
    Supports priority dispatching, visibility timeouts, lease heartbeats,
    dead-letter queues (DLQ), delayed execution, and task cancellation.
    """

    def __init__(self, visibility_timeout_seconds: float = 30.0):
        self.visibility_timeout = visibility_timeout_seconds
        self._items: dict[str, QueueItem] = {}
        self._dead_letter_queue: list[QueueItem] = []

    def enqueue(
        self,
        task_id: str,
        payload: dict[str, Any],
        priority: int = TaskPriority.NORMAL,
        pool_type: str = "GENERAL_WORKERS",
        delay_seconds: float = 0.0,
    ) -> QueueItem:
        item = QueueItem(
            task_id=task_id,
            payload=payload,
            priority=priority,
            pool_type=pool_type,
            delayed_until=time.time() + delay_seconds if delay_seconds > 0 else 0.0,
        )
        self._items[item.id] = item
        return item

    def lease_next_task(self, worker_id: str, pool_type: Optional[str] = None) -> Optional[QueueItem]:
        now = time.time()
        candidates = []

        for item in self._items.values():
            if item.status == TaskStatus.PENDING or (item.status == TaskStatus.LEASED and item.lease_expires_at < now):
                if item.delayed_until <= now:
                    if pool_type is None or item.pool_type == pool_type:
                        candidates.append(item)

        if not candidates:
            return None

        # Sort by priority descending, then created_at ascending
        candidates.sort(key=lambda x: (-x.priority, x.created_at))
        chosen = candidates[0]
        chosen.status = TaskStatus.LEASED
        chosen.lease_owner = worker_id
        chosen.lease_expires_at = now + self.visibility_timeout
        return chosen

    def heartbeat_lease(self, item_id: str, worker_id: str) -> bool:
        item = self._items.get(item_id)
        if not item or item.lease_owner != worker_id or item.status != TaskStatus.LEASED:
            return False
        item.lease_expires_at = time.time() + self.visibility_timeout
        return True

    def acknowledge_complete(self, item_id: str, worker_id: str) -> bool:
        item = self._items.get(item_id)
        if not item or item.lease_owner != worker_id:
            return False
        item.status = TaskStatus.COMPLETED
        item.completed_at = time.time()
        return True

    def fail_and_requeue(self, item_id: str, worker_id: str, error_message: str) -> bool:
        item = self._items.get(item_id)
        if not item:
            return False
        item.retry_count += 1
        item.error_message = error_message

        if item.retry_count >= item.max_retries:
            item.status = TaskStatus.DEAD_LETTER
            self._dead_letter_queue.append(item)
        else:
            item.status = TaskStatus.PENDING
            item.lease_owner = None
            item.lease_expires_at = 0.0
        return True

    def cancel_task(self, task_id: str) -> bool:
        for item in self._items.values():
            if item.task_id == task_id:
                item.status = TaskStatus.CANCELLED
                return True
        return False

    def get_queue_depth(self, pool_type: Optional[str] = None) -> int:
        now = time.time()
        return sum(
            1 for item in self._items.values()
            if item.status == TaskStatus.PENDING and item.delayed_until <= now and (pool_type is None or item.pool_type == pool_type)
        )

    def get_dead_letter_items(self) -> list[QueueItem]:
        return list(self._dead_letter_queue)


task_queue = DurableTaskQueue()
