import pytest
from datetime import datetime, timezone, timedelta
from app.memory.decay import MemoryDecayManager
from app.memory.models import MemoryRecord, MemoryType, FreshnessStatus


class TestMemoryDecay:
    def test_freshness_computation_and_decay(self):
        now = datetime.now(timezone.utc)
        
        # Fresh record
        fresh_rec = MemoryRecord(
            content="Today's news",
            memory_type=MemoryType.WORKING,
            created_at=now.isoformat(),
        )
        fresh_score = MemoryDecayManager.compute_freshness(fresh_rec, now)
        assert fresh_score >= 0.9

        # Old working memory (after 5 days) should decay dramatically
        old_working_time = now - timedelta(days=5)
        old_rec = MemoryRecord(
            content="Temporary calculation scratchpad",
            memory_type=MemoryType.WORKING,
            created_at=old_working_time.isoformat(),
        )
        old_score = MemoryDecayManager.compute_freshness(old_rec, now)
        assert old_score < 0.2

        # User preference should retain high score after 5 days
        pref_rec = MemoryRecord(
            content="Dark mode preference",
            memory_type=MemoryType.USER_PREFERENCE,
            created_at=old_working_time.isoformat(),
        )
        pref_score = MemoryDecayManager.compute_freshness(pref_rec, now)
        assert pref_score > 0.8
