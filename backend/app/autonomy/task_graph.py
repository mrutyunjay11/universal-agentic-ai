from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.tools.permissions import PermissionTier


class SubTaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SubTask(BaseModel):
    id: str = Field(default_factory=lambda: f"subtask_{uuid.uuid4().hex[:8]}")
    title: str
    objective: str
    parent_task_id: str
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    preferred_tools: list[str] = Field(default_factory=list)
    assigned_agent: Optional[str] = None
    permission_tier: PermissionTier = PermissionTier.READ
    status: SubTaskStatus = SubTaskStatus.PENDING
    priority: int = 1  # 1 (normal) to 10 (highest)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_output_schema: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class TaskGraph(BaseModel):
    """
    Topological Dependency Acyclic Graph (DAG) for managing multi-agent subtasks.
    Provides dependency tracking, ready task discovery, cycle prevention, and completion queries.
    """
    graph_id: str = Field(default_factory=lambda: f"tgraph_{uuid.uuid4().hex[:8]}")
    master_task_id: str
    nodes: dict[str, SubTask] = Field(default_factory=dict)

    def add_subtask(self, subtask: SubTask) -> None:
        self.nodes[subtask.id] = subtask

    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        return self.nodes.get(subtask_id)

    def get_ready_subtasks(self) -> list[SubTask]:
        """Returns all subtasks whose dependencies have successfully completed."""
        ready: list[SubTask] = []
        for subtask in self.nodes.values():
            if subtask.status in (SubTaskStatus.PENDING, SubTaskStatus.READY):
                deps_met = all(
                    dep in self.nodes and self.nodes[dep].status == SubTaskStatus.COMPLETED
                    for dep in subtask.dependencies
                )
                if deps_met:
                    subtask.status = SubTaskStatus.READY
                    ready.append(subtask)
        # Sort by priority descending
        return sorted(ready, key=lambda s: s.priority, reverse=True)

    def is_completed(self) -> bool:
        """Returns True if all subtasks have finished (completed, failed, or cancelled)."""
        if not self.nodes:
            return True
        return all(
            s.status in (SubTaskStatus.COMPLETED, SubTaskStatus.FAILED, SubTaskStatus.CANCELLED)
            for s in self.nodes.values()
        )

    def has_failures(self) -> bool:
        return any(s.status == SubTaskStatus.FAILED for s in self.nodes.values())

    def is_acyclic(self) -> bool:
        """Validates that graph contains no circular dependency cycles."""
        in_degree = {s_id: 0 for s_id in self.nodes}
        adj: dict[str, list[str]] = {s_id: [] for s_id in self.nodes}

        for s_id, subtask in self.nodes.items():
            for dep in subtask.dependencies:
                if dep in self.nodes:
                    adj[dep].append(s_id)
                    in_degree[s_id] += 1

        queue = [s_id for s_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited_count == len(self.nodes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "master_task_id": self.master_task_id,
            "total_nodes": len(self.nodes),
            "completed_nodes": sum(1 for s in self.nodes.values() if s.status == SubTaskStatus.COMPLETED),
            "nodes": {s_id: s.model_dump() for s_id, s in self.nodes.items()},
        }
