from __future__ import annotations
import json
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.autonomy.task_graph import TaskGraph


class CheckpointRecord(BaseModel):
    checkpoint_id: str
    task_id: str
    stage_name: str
    graph_snapshot: dict[str, Any]
    timestamp: str


class LongHorizonManager:
    """
    Manages long-horizon execution state, intermediate checkpoint snapshots,
    pause/resume mechanisms, and state recovery after process interruptions.
    """

    def __init__(self):
        self._checkpoints: dict[str, list[CheckpointRecord]] = {}
        self._paused_tasks: set[str] = set()

    def save_checkpoint(
        self,
        task_id: str,
        stage_name: str,
        task_graph: TaskGraph,
    ) -> CheckpointRecord:
        import datetime
        cp = CheckpointRecord(
            checkpoint_id=f"cp_{task_id}_{len(self._checkpoints.get(task_id, [])) + 1}",
            task_id=task_id,
            stage_name=stage_name,
            graph_snapshot=task_graph.to_dict(),
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        if task_id not in self._checkpoints:
            self._checkpoints[task_id] = []
        self._checkpoints[task_id].append(cp)
        return cp

    def get_latest_checkpoint(self, task_id: str) -> Optional[CheckpointRecord]:
        records = self._checkpoints.get(task_id, [])
        return records[-1] if records else None

    def pause_task(self, task_id: str) -> None:
        self._paused_tasks.add(task_id)

    def resume_task(self, task_id: str) -> None:
        self._paused_tasks.discard(task_id)

    def is_paused(self, task_id: str) -> bool:
        return task_id in self._paused_tasks


long_horizon_manager = LongHorizonManager()
