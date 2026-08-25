from __future__ import annotations
import asyncio
from typing import Any, Callable, Optional
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus
from app.autonomy.policies import DelegationPolicy, default_delegation_policy


class AdvancedScheduler:
    """
    Dependency-aware and resource-aware scheduler supporting sequential,
    parallel, and priority-based task dispatching within configured concurrency limits.
    """

    def __init__(self, policy: Optional[DelegationPolicy] = None):
        self.policy = policy or default_delegation_policy

    async def schedule_and_execute(
        self,
        task_graph: TaskGraph,
        executor_fn: Callable[[SubTask], Any],
    ) -> list[Any]:
        """
        Executes subtasks in parallel batches as their dependencies are satisfied.
        """
        results: list[Any] = []

        while not task_graph.is_completed():
            ready_tasks = task_graph.get_ready_subtasks()

            if not ready_tasks:
                # Check for deadlock
                pending = [s for s in task_graph.nodes.values() if s.status in (SubTaskStatus.PENDING, SubTaskStatus.BLOCKED)]
                if pending:
                    # Break deadlock by marking first blocked task as ready or failed
                    pending[0].status = SubTaskStatus.FAILED
                    pending[0].error = "Deadlock detected: dependencies unresolvable"
                break

            # Limit concurrency to max_parallel_agents
            batch = ready_tasks[:self.policy.max_parallel_agents]

            # Execute batch concurrently
            batch_coros = [executor_fn(task) for task in batch]
            batch_results = await asyncio.gather(*batch_coros, return_exceptions=True)

            for res in batch_results:
                if not isinstance(res, Exception):
                    results.append(res)

        return results


advanced_scheduler = AdvancedScheduler()
