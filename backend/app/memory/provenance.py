from __future__ import annotations
import hashlib
from typing import Any, Optional
from app.memory.models import MemoryRecord, VerificationStatus
from app.tools.provenance import ProvenanceRecord, SourceType, compute_content_hash


class MemoryProvenanceManager:
    """
    Manages provenance attribution and verification linkage for MemoryRecords.
    Ensures every persistent factual claim can be traced back to its underlying sources.
    """

    @staticmethod
    def attach_source(
        record: MemoryRecord,
        source_uri: str,
        source_id: Optional[str] = None,
        source_content: Optional[str] = None,
    ) -> MemoryRecord:
        """Attaches source URI, ID, and content hash to a memory record."""
        record.source = source_uri
        if source_id and source_id not in record.source_ids:
            record.source_ids.append(source_id)
        if source_content:
            record.metadata["source_content_hash"] = compute_content_hash(source_content)
        return record

    @staticmethod
    def attach_verification_result(
        record: MemoryRecord,
        verdict: str,
        confidence: float,
        evidence_sources: Optional[list[dict[str, Any]]] = None,
        verified_at: Optional[str] = None,
    ) -> MemoryRecord:
        """Attaches verification verdict details and updates status accordingly."""
        record.confidence = max(0.0, min(1.0, confidence))
        if verdict in ("verified", "VERIFIED"):
            record.verification_status = VerificationStatus.VERIFIED
        elif verdict in ("supported", "SUPPORTED", "partially_verified"):
            record.verification_status = VerificationStatus.SUPPORTED
        elif verdict in ("disputed", "DISPUTED", "refuted", "REFUTED"):
            record.verification_status = VerificationStatus.DISPUTED
        else:
            record.verification_status = VerificationStatus.UNVERIFIED

        if evidence_sources:
            for ev in evidence_sources:
                if isinstance(ev, dict) and "uri" in ev:
                    if ev["uri"] not in record.source_ids:
                        record.source_ids.append(ev["uri"])
        
        record.metadata["last_verification"] = {
            "verdict": verdict,
            "confidence": confidence,
            "verified_at": verified_at,
        }
        return record

    @staticmethod
    def verify_provenance_integrity(record: MemoryRecord) -> tuple[bool, str]:
        """Validates that a persistent fact or source memory possesses verifiable origin metadata."""
        if not record.source and not record.source_ids:
            return False, "Memory record has no origin source or source_ids attached"
        return True, "Valid provenance metadata"


memory_provenance = MemoryProvenanceManager()
