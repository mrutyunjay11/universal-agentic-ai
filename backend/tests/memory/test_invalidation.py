import pytest
from app.memory.invalidation import InvalidationManager
from app.memory.models import MemoryRecord, FreshnessStatus, VerificationStatus


class TestMemoryInvalidation:
    def test_supersede_and_invalidate(self):
        invalidator = InvalidationManager()

        old_rec = MemoryRecord(
            id="mem_old",
            content="Library X version 3 uses method foo()",
            freshness_status=FreshnessStatus.CURRENT,
            verification_status=VerificationStatus.VERIFIED,
        )

        new_rec = MemoryRecord(
            id="mem_new",
            content="Library X version 4 deprecated method foo() in favor of bar()",
            freshness_status=FreshnessStatus.CURRENT,
            verification_status=VerificationStatus.VERIFIED,
        )

        audit = invalidator.supersede_memory(
            old_record=old_rec,
            new_record=new_rec,
            reason="Version upgrade from v3 to v4",
        )

        assert old_rec.freshness_status == FreshnessStatus.SUPERSEDED
        assert old_rec.verification_status == VerificationStatus.SUPERSEDED
        assert old_rec.superseded_by == "mem_new"
        assert audit.memory_id == "mem_old"
        assert audit.superseded_by == "mem_new"
        assert len(invalidator.audit_log) == 1

        # Test explicit invalidation
        inv_audit = invalidator.invalidate_memory(
            record=old_rec,
            reason="Direct contradiction confirmed",
            new_status=FreshnessStatus.CONTRADICTED,
        )
        assert old_rec.freshness_status == FreshnessStatus.CONTRADICTED
        assert old_rec.verification_status == VerificationStatus.DISPUTED
        assert len(invalidator.audit_log) == 2
