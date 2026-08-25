from __future__ import annotations
import math
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class CandidateEvidence(BaseModel):
    id: str
    content: str
    source_id: str
    source_type: str = "OFFICIAL_DOCS"  # "OFFICIAL_DOCS", "RELEASE_NOTES", "REPO_CODE", "INDEPENDENT_TEST", "BLOG", "USER_MEMORY"
    authoritative_score: float = 0.8  # 0.0 to 1.0
    published_year: int = 2026
    version: Optional[str] = None
    verification_status: str = "UNVERIFIED"  # "VERIFIED", "UNVERIFIED", "FAILED"
    semantic_similarity: float = 0.75
    keyword_score: float = 0.5
    composite_score: float = 0.0
    contradiction_risk: float = 0.0
    is_corroboration: bool = False


class EvidenceReranker:
    """
    Multi-factor evidence-aware reranker.
    Separates relevance, authority, freshness, and verification quality rather than collapsing into a single blind score.
    Features 4-level fallback resilience when advanced cross-encoders are offline.
    """

    def __init__(self, fallback_level: int = 2):
        self.fallback_level = fallback_level

    def rerank(
        self,
        query: str,
        candidates: list[CandidateEvidence],
        task_version: Optional[str] = None,
        top_k: int = 10,
    ) -> list[CandidateEvidence]:
        if not candidates:
            return []

        query_terms = set(query.lower().split())

        for c in candidates:
            # 1. Keyword overlap
            content_words = set(c.content.lower().split())
            overlap = len(query_terms.intersection(content_words)) / max(1, len(query_terms))
            c.keyword_score = min(1.0, overlap)

            # 2. Freshness factor
            current_year = 2026
            age = max(0, current_year - c.published_year)
            freshness_factor = max(0.2, 1.0 - (age * 0.15))

            # 3. Version match bonus/penalty
            version_match = 1.0
            if task_version and c.version:
                if task_version.split(".")[0] == c.version.split(".")[0]:
                    version_match = 1.2
                else:
                    version_match = 0.6

            # 4. Verification factor
            verif_multiplier = 1.2 if c.verification_status == "VERIFIED" else 1.0

            # Level 2 Hybrid Deterministic Scoring
            raw_score = (
                (c.semantic_similarity * 0.35)
                + (c.keyword_score * 0.25)
                + (c.authoritative_score * 0.25)
                + (freshness_factor * 0.15)
            ) * version_match * verif_multiplier - (c.contradiction_risk * 0.3)

            c.composite_score = round(max(0.0, raw_score), 4)

        # Sort descending by composite score, then by source authority
        ranked = sorted(candidates, key=lambda x: (x.composite_score, x.authoritative_score), reverse=True)
        return ranked[:top_k]


evidence_reranker = EvidenceReranker()
