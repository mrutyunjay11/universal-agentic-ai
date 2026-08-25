from __future__ import annotations
import math
from datetime import datetime, timezone
from app.memory.models import MemoryRecord, MemoryType, FreshnessStatus


class MemoryDecayManager:
    """
    Computes time-based freshness decay, half-life calculations, and access frequency adjustments.
    Prevents old or temporary memories from retaining inappropriate permanent priority.
    """

    # Half-life duration in days per memory type
    HALF_LIVES_DAYS: dict[MemoryType, float] = {
        MemoryType.WORKING: 0.1,          # ~2.4 hours
        MemoryType.EPISODIC: 14.0,        # 2 weeks
        MemoryType.SEMANTIC: 180.0,       # 6 months
        MemoryType.PROCEDURAL: 90.0,      # 3 months
        MemoryType.PROJECT: 60.0,         # 2 months
        MemoryType.USER_PREFERENCE: 365.0,# 1 year
        MemoryType.FACT: 120.0,           # 4 months
        MemoryType.TASK_HISTORY: 30.0,    # 1 month
        MemoryType.SOURCE_MEMORY: 90.0,   # 3 months
    }

    @classmethod
    def compute_freshness(cls, record: MemoryRecord, current_time: datetime | None = None) -> float:
        """
        Calculates freshness score in [0.0, 1.0] using exponential decay and access frequency boosts.
        """
        now = current_time or datetime.now(timezone.utc)
        
        # Check explicit expiration
        if record.expires_at:
            try:
                exp_dt = datetime.fromisoformat(record.expires_at)
                if now >= exp_dt:
                    return 0.0
            except Exception:
                pass

        if record.freshness_status in (FreshnessStatus.EXPIRED, FreshnessStatus.SUPERSEDED, FreshnessStatus.CONTRADICTED):
            return 0.0

        if record.freshness_status == FreshnessStatus.STALE:
            return 0.2

        try:
            created_dt = datetime.fromisoformat(record.created_at)
            age_days = max(0.0, (now - created_dt).total_seconds() / 86400.0)
        except Exception:
            age_days = 0.0

        half_life = cls.HALF_LIVES_DAYS.get(record.memory_type, 60.0)
        
        # Exponential half-life decay: N(t) = 0.5 ^ (t / t_half)
        base_decay = math.pow(0.5, age_days / half_life)
        
        # Access frequency boost: log(1 + access_count) capped at +0.3
        access_boost = min(0.3, math.log1p(record.access_count) * 0.05)
        
        freshness = max(0.05, min(1.0, base_decay + access_boost))
        return freshness

    @classmethod
    def check_stale_status(cls, record: MemoryRecord, current_time: datetime | None = None) -> FreshnessStatus:
        """Determines if a memory record has transitioned to STALE or EXPIRED."""
        now = current_time or datetime.now(timezone.utc)
        if record.expires_at:
            try:
                if now >= datetime.fromisoformat(record.expires_at):
                    return FreshnessStatus.EXPIRED
            except Exception:
                pass

        freshness = cls.compute_freshness(record, now)
        if freshness < 0.15 and record.freshness_status == FreshnessStatus.CURRENT:
            return FreshnessStatus.STALE
        return record.freshness_status


memory_decay = MemoryDecayManager()
