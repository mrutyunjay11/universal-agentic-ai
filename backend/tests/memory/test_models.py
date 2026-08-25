import pytest
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus, InvalidationRecord


class TestMemoryModels:
    def test_memory_record_defaults(self):
        rec = MemoryRecord(content="Python 3.12 is standard")
        assert rec.id.startswith("mem_")
        assert rec.memory_type == MemoryType.SEMANTIC
        assert rec.scope == MemoryScope.GLOBAL
        assert rec.confidence == 0.8
        assert rec.freshness_status == FreshnessStatus.CURRENT
        assert rec.verification_status == VerificationStatus.UNVERIFIED
        assert rec.access_count == 0

    def test_memory_record_mark_accessed(self):
        rec = MemoryRecord(content="FastAPI is fast")
        initial_time = rec.last_accessed_at
        rec.mark_accessed()
        assert rec.access_count == 1
        assert rec.last_accessed_at >= initial_time

    def test_invalidation_record_model(self):
        inv = InvalidationRecord(
            memory_id="mem_123",
            previous_status=FreshnessStatus.CURRENT,
            new_status=FreshnessStatus.SUPERSEDED,
            reason="Updated specs in official documentation",
        )
        assert inv.id.startswith("inv_")
        assert inv.new_status == FreshnessStatus.SUPERSEDED
        assert "Updated specs" in inv.reason
