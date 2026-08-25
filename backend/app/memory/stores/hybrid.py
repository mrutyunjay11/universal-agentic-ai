from __future__ import annotations
from typing import Optional
from app.memory.base import MemoryStore, EmbeddingProvider
from app.memory.models import MemoryRecord, MemoryType, MemoryScope
from app.memory.stores.sqlite import SQLiteMemoryStore
from app.memory.stores.vector import VectorMemoryStore
from app.memory.embeddings import get_embedding_provider


class HybridMemoryStore(MemoryStore):
    """
    Hybrid memory store unifying SQLite metadata persistence and Vector semantic indexing.
    """

    def __init__(
        self,
        sqlite_store: Optional[SQLiteMemoryStore] = None,
        vector_store: Optional[VectorMemoryStore] = None,
        embedder: Optional[EmbeddingProvider] = None,
    ):
        self.embedder = embedder or get_embedding_provider()
        self.sqlite = sqlite_store or SQLiteMemoryStore(":memory:")
        self.vector = vector_store or VectorMemoryStore(self.embedder)

    async def initialize(self) -> None:
        await self.sqlite.initialize()
        await self.vector.initialize()

    async def insert(self, record: MemoryRecord) -> MemoryRecord:
        if not record.embedding:
            text_to_embed = f"{record.content} {record.summary or ''}"
            record.embedding = await self.embedder.embed_text(text_to_embed)
        
        await self.sqlite.insert(record)
        await self.vector.insert(record)
        return record

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        rec = await self.sqlite.get(memory_id)
        if rec:
            return rec
        return await self.vector.get(memory_id)

    async def update(self, record: MemoryRecord) -> MemoryRecord:
        if not record.embedding:
            text_to_embed = f"{record.content} {record.summary or ''}"
            record.embedding = await self.embedder.embed_text(text_to_embed)
            
        await self.sqlite.update(record)
        await self.vector.update(record)
        return record

    async def delete(self, memory_id: str) -> bool:
        res1 = await self.sqlite.delete(memory_id)
        res2 = await self.vector.delete(memory_id)
        return res1 or res2

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
        # Perform dual search (semantic vector + structured keyword SQLite)
        vec_results = await self.vector.search(
            query=query,
            limit=limit * 2,
            memory_type=memory_type,
            scope=scope,
            project_id=project_id,
            user_id=user_id,
            task_id=task_id,
            tags=tags,
            min_confidence=min_confidence,
            include_stale=include_stale,
        )

        kw_results = await self.sqlite.search(
            query=query,
            limit=limit * 2,
            memory_type=memory_type,
            scope=scope,
            project_id=project_id,
            user_id=user_id,
            task_id=task_id,
            tags=tags,
            min_confidence=min_confidence,
            include_stale=include_stale,
        )

        # Merge with deduplication preserving ranking order
        seen_ids: set[str] = set()
        merged: list[MemoryRecord] = []

        # Interleave or merge results
        all_candidates = vec_results + kw_results
        for record in all_candidates:
            if record.id not in seen_ids:
                seen_ids.add(record.id)
                merged.append(record)
            if len(merged) >= limit:
                break

        return merged

    async def list_all(
        self,
        limit: int = 100,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        return await self.sqlite.list_all(limit=limit, memory_type=memory_type, project_id=project_id, user_id=user_id)

    async def count(
        self,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        return await self.sqlite.count(memory_type=memory_type, project_id=project_id, user_id=user_id)

    async def clear(self) -> None:
        await self.sqlite.clear()
        await self.vector.clear()
