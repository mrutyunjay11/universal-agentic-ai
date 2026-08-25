from __future__ import annotations
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class RetrievalCandidate(BaseModel):
    """
    Standardized retrieval candidate entity preserving full provenance,
    multi-signal scoring, source authority, and freshness.
    """

    candidate_id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    document_id: str
    chunk_id: str
    source_id: str
    content: str
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    fusion_score: float = 0.0
    reranker_score: float = 0.0
    metadata_score: float = 0.0
    source_authority: float = 0.8
    authoritative_score: float = 0.8
    published_year: int = 2026
    version: Optional[str] = None
    verification_status: str = "UNVERIFIED"  # "VERIFIED", "UNVERIFIED", "FAILED"
    provenance: dict[str, Any] = Field(default_factory=dict)
    source_type: str = "OFFICIAL_DOCS"
