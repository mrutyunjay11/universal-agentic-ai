from __future__ import annotations
import re
from typing import Any, Optional
from app.memory.base import MemoryStore, EmbeddingProvider
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, FreshnessStatus
from app.memory.ranking import MemoryRanker, memory_ranker
from app.memory.embeddings import get_embedding_provider


class MemoryRetriever:
    """
    Hybrid retrieval coordinator with query understanding, multi-scope filtering,
    semantic + keyword retrieval, and multi-factor score ranking.
    """

    def __init__(
        self,
        store: MemoryStore,
        embedder: Optional[EmbeddingProvider] = None,
        ranker: Optional[MemoryRanker] = None,
    ):
        self.store = store
        self.embedder = embedder or get_embedding_provider()
        self.ranker = ranker or memory_ranker

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
        Retrieves, ranks, and filters memories relevant to the query and context.
        """
        normalized_query = self._normalize_query(query)
        candidates: list[MemoryRecord] = []

        # 1. Fetch candidate pool across requested memory types or globally
        if memory_types:
            for m_type in memory_types:
                recs = await self.store.search(
                    query=normalized_query,
                    limit=limit * 3,
                    memory_type=m_type,
                    project_id=project_id,
                    user_id=user_id,
                    task_id=task_id,
                    include_stale=include_stale,
                )
                candidates.extend(recs)
        else:
            candidates = await self.store.search(
                query=normalized_query,
                limit=limit * 4,
                project_id=project_id,
                user_id=user_id,
                task_id=task_id,
                include_stale=include_stale,
            )

        # Deduplicate candidates
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c.id not in seen:
                seen.add(c.id)
                unique_candidates.append(c)

        if not unique_candidates:
            return []

        # 2. Compute semantic vector similarities if query is non-empty
        semantic_map: dict[str, float] = {}
        if normalized_query.strip():
            query_vec = await self.embedder.embed_text(normalized_query)
            for c in unique_candidates:
                if c.embedding:
                    from app.memory.stores.vector import cosine_similarity
                    semantic_map[c.id] = max(0.0, cosine_similarity(query_vec, c.embedding))
                else:
                    semantic_map[c.id] = c.relevance

        # 3. Apply Multi-Factor Ranker
        ranked = self.ranker.rank(
            query=normalized_query,
            records=unique_candidates,
            semantic_scores=semantic_map,
            current_project_id=project_id,
            current_user_id=user_id,
        )

        # 4. Filter by minimum composite score threshold and limit
        filtered = [(score, rec) for score, rec in ranked if score >= min_score][:limit]
        
        # Mark retrieved records as accessed
        for _, rec in filtered:
            rec.mark_accessed()
            # Asynchronously update in store
            try:
                await self.store.update(rec)
            except Exception:
                pass

        return filtered

    def _normalize_query(self, raw_query: str) -> str:
        """Enriches and cleans query string for higher retrieval recall."""
        # Strip common punctuation and leading conversational noise
        cleaned = re.sub(r"^(?:please\s+|can you\s+|how do i\s+|what is\s+|tell me about\s+)", "", raw_query, flags=re.IGNORECASE).strip()
        return cleaned
