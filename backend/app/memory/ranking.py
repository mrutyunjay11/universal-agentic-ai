from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from app.memory.models import MemoryRecord, VerificationStatus, FreshnessStatus
from app.memory.decay import memory_decay


@dataclass
class RankingWeights:
    """Configurable multi-factor ranking weights."""
    semantic_similarity: float = 0.30
    keyword_match: float = 0.15
    task_relevance: float = 0.15
    project_relevance: float = 0.10
    importance: float = 0.10
    verification_quality: float = 0.10
    freshness: float = 0.10
    contradiction_penalty: float = 0.50
    stale_penalty: float = 0.30


class MemoryRanker:
    """
    Multi-factor hybrid ranking engine combining semantic similarity, keyword matching,
    task/project relevance, importance, freshness decay, and verification confidence.
    """

    def __init__(self, weights: Optional[RankingWeights] = None):
        self.weights = weights or RankingWeights()

    def rank(
        self,
        query: str,
        records: list[MemoryRecord],
        semantic_scores: Optional[dict[str, float]] = None,
        current_task_type: Optional[str] = None,
        current_project_id: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> list[tuple[float, MemoryRecord]]:
        """
        Ranks a list of candidate memory records and returns sorted (score, record) tuples.
        """
        scored_records: list[tuple[float, MemoryRecord]] = []
        semantic_map = semantic_scores or {}
        q_tokens = set(query.lower().strip().split()) if query else set()

        for record in records:
            # 1. Semantic Similarity
            sem_score = semantic_map.get(record.id, record.relevance)

            # 2. Keyword Match Ratio
            kw_score = 0.0
            if q_tokens:
                rec_text = f"{record.content} {record.summary or ''} {' '.join(record.tags)}".lower()
                matches = sum(1 for t in q_tokens if t in rec_text)
                kw_score = matches / len(q_tokens)

            # 3. Task Relevance
            task_rel = 1.0 if (record.task_id and current_task_type and current_task_type.lower() in record.content.lower()) else record.relevance

            # 4. Project & User Relevance
            proj_rel = 1.0 if (record.project_id and record.project_id == current_project_id) else (0.7 if record.scope.value == "GLOBAL" else 0.3)
            user_rel = 1.0 if (record.user_id and record.user_id == current_user_id) else (0.7 if record.user_id is None else 0.2)
            scope_rel = (proj_rel + user_rel) / 2.0

            # 5. Importance & Verification Quality
            imp_score = record.importance
            ver_score = 1.0 if record.verification_status == VerificationStatus.VERIFIED else (
                0.7 if record.verification_status == VerificationStatus.SUPPORTED else 0.3
            )

            # 6. Freshness
            fresh_score = memory_decay.compute_freshness(record)

            # Base weighted sum
            total_score = (
                self.weights.semantic_similarity * sem_score
                + self.weights.keyword_match * kw_score
                + self.weights.task_relevance * task_rel
                + self.weights.project_relevance * scope_rel
                + self.weights.importance * imp_score
                + self.weights.verification_quality * ver_score
                + self.weights.freshness * fresh_score
            )

            # Apply Penalties
            if record.freshness_status in (FreshnessStatus.CONTRADICTED, FreshnessStatus.SUPERSEDED) or record.verification_status == VerificationStatus.SUPERSEDED:
                total_score -= self.weights.contradiction_penalty
            elif record.freshness_status in (FreshnessStatus.STALE, FreshnessStatus.EXPIRED) or record.verification_status == VerificationStatus.EXPIRED:
                total_score -= self.weights.stale_penalty

            score = max(0.0, min(1.0, total_score))
            scored_records.append((score, record))

        # Sort descending by composite score
        scored_records.sort(key=lambda x: x[0], reverse=True)
        return scored_records


memory_ranker = MemoryRanker()
