from __future__ import annotations
from typing import Any, Optional
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus
from app.autonomy.policies import DelegationPolicy, default_delegation_policy


class HierarchicalSupervisor:
    """
    Supervises multi-agent execution hierarchy.
    Enforces subtask retry limits, reassigns failed tasks, and terminates redundant work.
    """

    def __init__(self, policy: Optional[DelegationPolicy] = None):
        self.policy = policy or default_delegation_policy

    def handle_subtask_failure(
        self,
        subtask: SubTask,
        task_graph: TaskGraph,
    ) -> bool:
        """Decides whether to retry, reassign, or fail subtask."""
        if subtask.retry_count < self.policy.max_retries_per_subtask:
            subtask.retry_count += 1
            subtask.status = SubTaskStatus.READY
            # Attempt fallback agent assignment
            subtask.assigned_agent = "GeneralistAgent"
            return True
        else:
            subtask.status = SubTaskStatus.FAILED
            # Cascade fail or block dependent nodes
            for other_id, other_node in task_graph.nodes.items():
                if subtask.id in other_node.dependencies:
                    other_node.status = SubTaskStatus.BLOCKED
            return False


hierarchical_supervisor = HierarchicalSupervisor()
