from __future__ import annotations
import time
from typing import Any, Optional
from app.autonomy.task_graph import TaskGraph, SubTaskStatus


class Watchdog:
    """
    Monitors long-running multi-agent execution, detects stalls, deadlocks (circular wait dependencies),
    and enforces execution timeouts.
    """

    def __init__(self, stall_timeout_seconds: float = 60.0):
        self.stall_timeout = stall_timeout_seconds
        self._last_progress_time = time.time()

    def record_progress(self) -> None:
        self._last_progress_time = time.time()

    def check_for_stalls(self) -> bool:
        """Returns True if execution has stalled without progress exceeding timeout."""
        return (time.time() - self._last_progress_time) > self.stall_timeout

    def detect_deadlocks(self, task_graph: TaskGraph) -> list[str]:
        """Detects circular wait cycles in task dependencies."""
        deadlocked_tasks: list[str] = []
        if not task_graph.is_acyclic():
            for s_id, s in task_graph.nodes.items():
                if s.status in (SubTaskStatus.PENDING, SubTaskStatus.BLOCKED):
                    deadlocked_tasks.append(s_id)
        return deadlocked_tasks


watchdog = Watchdog()
