from __future__ import annotations
import hashlib
from typing import Any
from app.context.reranker import CandidateEvidence


class ContextDeduplicator:
    """
    Deduplicates candidate evidence chunks.
    Crucially distinguishes between redundant duplicates from the same origin vs
    independent multi-source corroboration across different publishers or test runs.
    """

    def deduplicate(
        self,
        candidates: list[CandidateEvidence],
        similarity_threshold: float = 0.85,
    ) -> tuple[list[CandidateEvidence], list[CandidateEvidence]]:
        """
        Returns (unique_evidence_list, independent_corroborations_list).
        """
        unique: list[CandidateEvidence] = []
        corroborations: list[CandidateEvidence] = []
        seen_hashes: set[str] = set()

        for c in candidates:
            # Normalize content hash
            norm = "".join(c.content.lower().split())
            c_hash = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

            if c_hash in seen_hashes:
                # Check if this is from a different source type -> Corroboration!
                existing = next((u for u in unique if hashlib.sha256("".join(u.content.lower().split()).encode("utf-8")).hexdigest()[:16] == c_hash), None)
                if existing and existing.source_type != c.source_type:
                    c.is_corroboration = True
                    corroborations.append(c)
                continue

            seen_hashes.add(c_hash)
            unique.append(c)

        return unique, corroborations


context_deduplicator = ContextDeduplicator()
