from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from app.memory.models import MemoryRecord, InvalidationRecord, FreshnessStatus, VerificationStatus


class InvalidationManager:
    """
    Handles knowledge invalidation, stale version detection, and contradictory record superseding.
    Preserves audit history rather than silently erasing records.
    """

    def __init__(self):
        self._audit_log: list[InvalidationRecord] = []

    @property
    def audit_log(self) -> list[InvalidationRecord]:
        return self._audit_log

    def supersede_memory(
        self,
        old_record: MemoryRecord,
        new_record: MemoryRecord,
        reason: str = "New evidence or updated documentation superseded previous knowledge",
        actor: str = "agent_reflection",
    ) -> InvalidationRecord:
        """Marks old_record as SUPERSEDED and links it to new_record."""
        prev_status = old_record.freshness_status
        old_record.freshness_status = FreshnessStatus.SUPERSEDED
        old_record.verification_status = VerificationStatus.SUPERSEDED
        old_record.superseded_by = new_record.id
        old_record.updated_at = datetime.now(timezone.utc).isoformat()

        audit = InvalidationRecord(
            memory_id=old_record.id,
            previous_status=prev_status,
            new_status=FreshnessStatus.SUPERSEDED,
            reason=reason,
            superseded_by=new_record.id,
            actor=actor,
        )
        self._audit_log.append(audit)
        return audit

    def invalidate_memory(
        self,
        record: MemoryRecord,
        reason: str,
        new_status: FreshnessStatus = FreshnessStatus.CONTRADICTED,
        actor: str = "user_correction",
    ) -> InvalidationRecord:
        """Explicitly marks a memory as CONTRADICTED, STALE, or EXPIRED with full audit logging."""
        prev_status = record.freshness_status
        record.freshness_status = new_status
        if new_status == FreshnessStatus.CONTRADICTED:
            record.verification_status = VerificationStatus.DISPUTED
        elif new_status == FreshnessStatus.EXPIRED:
            record.verification_status = VerificationStatus.EXPIRED

        record.updated_at = datetime.now(timezone.utc).isoformat()

        audit = InvalidationRecord(
            memory_id=record.id,
            previous_status=prev_status,
            new_status=new_status,
            reason=reason,
            actor=actor,
        )
        self._audit_log.append(audit)
        return audit


invalidation_manager = InvalidationManager()
