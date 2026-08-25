from __future__ import annotations
import math
from typing import Optional
from app.memory.base import MemoryStore, EmbeddingProvider
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, FreshnessStatus
from app.memory.embeddings import get_embedding_provider


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 < 1e-9 or norm2 < 1e-9:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm1 * norm2)))


class VectorMemoryStore(MemoryStore):
    """
    Provider-agnostic in-memory / local vector memory store.
    Computes semantic cosine similarity over embeddings while enforcing scope and metadata filters.
    """

    def __init__(self, embedder: Optional[EmbeddingProvider] = None):
        self.embedder = embedder or get_embedding_provider()
        self._records: dict[str, MemoryRecord] = {}

    async def initialize(self) -> None:
        pass

    async def insert(self, record: MemoryRecord) -> MemoryRecord:
        if not record.embedding:
            text_to_embed = f"{record.content} {record.summary or ''}"
            record.embedding = await self.embedder.embed_text(text_to_embed)
        self._records[record.id] = record
        return record

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        return self._records.get(memory_id)

    async def update(self, record: MemoryRecord) -> MemoryRecord:
        if not record.embedding:
            text_to_embed = f"{record.content} {record.summary or ''}"
            record.embedding = await self.embedder.embed_text(text_to_embed)
        self._records[record.id] = record
        return record

    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._records:
            del self._records[memory_id]
            return True
        return False

    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        scope: Optional[MemoryScope] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_confidence: float = 0.0,
        include_stale: bool = False,
    ) -> list[MemoryRecord]:
        if not self._records:
            return []

        query_vec = await self.embedder.embed_text(query) if query.strip() else None

        scored: list[tuple[float, MemoryRecord]] = []

        for record in self._records.values():
            if record.confidence < min_confidence:
                continue

            if not include_stale and record.freshness_status not in (FreshnessStatus.CURRENT, FreshnessStatus.UNKNOWN):
                continue

            if memory_type and record.memory_type != memory_type:
                continue

            if scope and record.scope != scope:
                continue

            if project_id and record.project_id != project_id and record.scope != MemoryScope.GLOBAL:
                continue

            if user_id and record.user_id != user_id and record.user_id is not None:
                continue

            if task_id and record.task_id != task_id:
                continue

            if tags and not any(t in record.tags for t in tags):
                continue

            # Calculate semantic similarity
            if query_vec and record.embedding:
                sim = cosine_similarity(query_vec, record.embedding)
            else:
                sim = record.importance

            scored.append((sim, record))

        # Sort descending by similarity score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:limit]]

    async def list_all(
        self,
        limit: int = 100,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        results = []
        for r in self._records.values():
            if memory_type and r.memory_type != memory_type:
                continue
            if project_id and r.project_id != project_id:
                continue
            if user_id and r.user_id != user_id:
                continue
            results.append(r)
        return results[:limit]

    async def count(
        self,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        return len(await self.list_all(limit=100000, memory_type=memory_type, project_id=project_id, user_id=user_id))

    async def clear(self) -> None:
        self._records.clear()
