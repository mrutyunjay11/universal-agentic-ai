from __future__ import annotations
import logging
from typing import Any, Optional
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus, InvalidationRecord
from app.memory.base import MemoryStore, EmbeddingProvider
from app.memory.stores.hybrid import HybridMemoryStore
from app.memory.stores.sqlite import SQLiteMemoryStore
from app.memory.stores.vector import VectorMemoryStore
from app.memory.embeddings import get_embedding_provider
from app.memory.retrieval import MemoryRetriever
from app.memory.ranking import MemoryRanker, memory_ranker
from app.memory.invalidation import InvalidationManager, invalidation_manager
from app.memory.consolidation import MemoryConsolidator
from app.memory.context_builder import HierarchicalContextBuilder, context_builder
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central orchestrator for Phase 3 Memory, Knowledge, Context, Retrieval, and Learning.
    Guarantees tenant/user/project isolation, provenance tracking, and decay-aware retrieval.
    """

    def __init__(
        self,
        store: Optional[MemoryStore] = None,
        embedder: Optional[EmbeddingProvider] = None,
        ranker: Optional[MemoryRanker] = None,
    ):
        self.embedder = embedder or get_embedding_provider()
        self.store = store or HybridMemoryStore(
            sqlite_store=SQLiteMemoryStore(":memory:"),
            vector_store=VectorMemoryStore(self.embedder),
            embedder=self.embedder,
        )
        self.ranker = ranker or memory_ranker
        self.retriever = MemoryRetriever(self.store, self.embedder, self.ranker)
        self.invalidator = invalidation_manager
        self.consolidator = MemoryConsolidator(self.store)
        self.context_builder = context_builder

    async def initialize(self) -> None:
        """Initializes underlying memory storage backends."""
        await self.store.initialize()

    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        scope: MemoryScope = MemoryScope.GLOBAL,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        source_ids: Optional[list[str]] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        confidence: float = 0.8,
        importance: float = 0.5,
        verification_status: VerificationStatus = VerificationStatus.UNVERIFIED,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Stores a new memory record into the system with isolation enforcement."""
        freshness = FreshnessStatus.CURRENT
        if verification_status == VerificationStatus.SUPERSEDED:
            freshness = FreshnessStatus.SUPERSEDED
        elif verification_status == VerificationStatus.EXPIRED:
            freshness = FreshnessStatus.EXPIRED
        elif verification_status == VerificationStatus.DISPUTED:
            freshness = FreshnessStatus.CONTRADICTED

        record = MemoryRecord(
            content=content,
            memory_type=memory_type,
            scope=scope,
            summary=summary,
            source=source,
            source_ids=source_ids or [],
            project_id=project_id,
            user_id=user_id,
            task_id=task_id,
            confidence=confidence,
            importance=importance,
            verification_status=verification_status,
            freshness_status=freshness,
            tags=tags or [],
            metadata=metadata or {},
        )
        return await self.store.insert(record)

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        memory_types: Optional[list[MemoryType]] = None,
        min_score: float = 0.35,
        include_stale: bool = False,
    ) -> list[tuple[float, MemoryRecord]]:
        """
        Retrieves top relevant memories with strict scope and security isolation.
        """
        return await self.retriever.retrieve(
            query=query,
            limit=limit,
            project_id=project_id,
            user_id=user_id,
            task_id=task_id,
            memory_types=memory_types,
            min_score=min_score,
            include_stale=include_stale,
        )

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        return await self.store.get(memory_id)

    async def update(self, record: MemoryRecord) -> MemoryRecord:
        return await self.store.update(record)

    async def forget(self, memory_id: str) -> bool:
        """Explicitly deletes a memory record."""
        return await self.store.delete(memory_id)

    async def invalidate(
        self,
        memory_id: str,
        reason: str,
        new_status: FreshnessStatus = FreshnessStatus.CONTRADICTED,
        actor: str = "system",
    ) -> Optional[InvalidationRecord]:
        """Marks a memory as superseded or invalidated without deleting historical context."""
        rec = await self.store.get(memory_id)
        if not rec:
            return None
        audit = self.invalidator.invalidate_memory(rec, reason=reason, new_status=new_status, actor=actor)
        await self.store.update(rec)
        return audit

    async def supersede(
        self,
        old_memory_id: str,
        new_memory: MemoryRecord,
        reason: str = "Updated with new verified evidence",
    ) -> Optional[InvalidationRecord]:
        """Supersedes an old memory record with a newly created record."""
        old_rec = await self.store.get(old_memory_id)
        if not old_rec:
            return None
        await self.store.insert(new_memory)
        audit = self.invalidator.supersede_memory(old_rec, new_memory, reason=reason)
        await self.store.update(old_rec)
        return audit

    async def consolidate_task(
        self,
        state: AgentState,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        """Consolidates completed task state into persistent memories."""
        return await self.consolidator.consolidate_task(state, project_id=project_id, user_id=user_id)

    def build_context(
        self,
        state: AgentState,
        retrieved_memories: Optional[list[tuple[float, MemoryRecord]]] = None,
        system_instruction: Optional[str] = None,
    ) -> dict[str, Any]:
        """Assembles budgeted multi-slot prompt context."""
        return self.context_builder.build_prompt_context(
            state=state,
            retrieved_memories=retrieved_memories,
            system_instruction=system_instruction,
        )

    async def count(self, memory_type: Optional[MemoryType] = None, project_id: Optional[str] = None, user_id: Optional[str] = None) -> int:
        return await self.store.count(memory_type=memory_type, project_id=project_id, user_id=user_id)

    async def clear(self) -> None:
        await self.store.clear()


memory_manager = MemoryManager()
