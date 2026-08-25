from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskMemoryEntry(BaseModel):
    key: str
    value: Any
    category: str = "fact"  # fact, intermediate_output, decision, checkpoint
    step_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class TaskMemory:
    """Short-term task memory for tracking intermediate state, facts, decisions, and variable assignments during a single task run."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self._store: dict[str, TaskMemoryEntry] = {}

    def set(self, key: str, value: Any, category: str = "fact", step_id: Optional[str] = None):
        self._store[key] = TaskMemoryEntry(
            key=key,
            value=value,
            category=category,
            step_id=step_id,
            created_at=time.time(),
        )

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        return entry.value if entry else default

    def list_entries(self, category: Optional[str] = None) -> list[TaskMemoryEntry]:
        if category:
            return [e for e in self._store.values() if e.category == category]
        return list(self._store.values())

    def clear(self):
        self._store.clear()
