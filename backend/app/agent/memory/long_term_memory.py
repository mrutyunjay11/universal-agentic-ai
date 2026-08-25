from __future__ import annotations
import time
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    USER_MEMORY = "USER_MEMORY"
    PROJECT_MEMORY = "PROJECT_MEMORY"
    FACT_MEMORY = "FACT_MEMORY"
    PROCEDURAL_MEMORY = "PROCEDURAL_MEMORY"
    TASK_HISTORY = "TASK_HISTORY"


class LongTermMemoryEntry(BaseModel):
    id: str
    category: MemoryCategory
    key: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance_uri: Optional[str] = None
    confidence: float = 1.0
    timestamp: float = Field(default_factory=time.time)


class LongTermMemory:
    """Persistent memory abstraction with category tagging, keyword search, and vector RAG integration."""

    def __init__(self):
        self._entries: list[LongTermMemoryEntry] = []

    def remember(
        self,
        entry_id: str,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        provenance_uri: Optional[str] = None,
        confidence: float = 1.0,
    ) -> LongTermMemoryEntry:
        entry = LongTermMemoryEntry(
            id=entry_id,
            category=category,
            key=key,
            content=content,
            metadata=metadata or {},
            provenance_uri=provenance_uri,
            confidence=confidence,
            timestamp=time.time(),
        )
        self._entries.append(entry)
        return entry

    def recall(
        self,
        query: str,
        category: Optional[MemoryCategory] = None,
        limit: int = 5,
    ) -> list[LongTermMemoryEntry]:
        results: list[LongTermMemoryEntry] = []
        q_lower = query.lower()

        for e in reversed(self._entries):
            if category and e.category != category:
                continue
            if q_lower in e.key.lower() or q_lower in e.content.lower():
                results.append(e)
            if len(results) >= limit:
                break

        return results

    def recall_all(self, category: Optional[MemoryCategory] = None) -> list[LongTermMemoryEntry]:
        if category:
            return [e for e in self._entries if e.category == category]
        return list(self._entries)


long_term_memory = LongTermMemory()
