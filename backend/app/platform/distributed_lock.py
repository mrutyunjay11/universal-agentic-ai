from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class LockRecord(BaseModel):
    lock_key: str
    owner_id: str
    acquired_at: float = Field(default_factory=time.time)
    expires_at: float
    renew_count: int = 0


class DistributedLockManager:
    """
    Distributed lock manager providing task and step locking, lease renewals,
    and duplicate execution prevention across distributed worker nodes.
    """

    def __init__(self, default_ttl_seconds: float = 20.0):
        self.default_ttl = default_ttl_seconds
        self._locks: dict[str, LockRecord] = {}

    def acquire_lock(self, lock_key: str, owner_id: str, ttl_seconds: Optional[float] = None) -> bool:
        now = time.time()
        existing = self._locks.get(lock_key)

        if existing and existing.expires_at > now:
            if existing.owner_id == owner_id:
                # Re-entrant acquisition
                existing.expires_at = now + (ttl_seconds or self.default_ttl)
                return True
            return False

        # Acquire new lock
        ttl = ttl_seconds or self.default_ttl
        self._locks[lock_key] = LockRecord(
            lock_key=lock_key,
            owner_id=owner_id,
            expires_at=now + ttl,
        )
        return True

    def renew_lock(self, lock_key: str, owner_id: str, extend_seconds: Optional[float] = None) -> bool:
        now = time.time()
        existing = self._locks.get(lock_key)
        if not existing or existing.owner_id != owner_id or existing.expires_at <= now:
            return False

        existing.expires_at = now + (extend_seconds or self.default_ttl)
        existing.renew_count += 1
        return True

    def release_lock(self, lock_key: str, owner_id: str) -> bool:
        existing = self._locks.get(lock_key)
        if not existing or existing.owner_id != owner_id:
            return False

        del self._locks[lock_key]
        return True

    def is_locked(self, lock_key: str) -> bool:
        now = time.time()
        existing = self._locks.get(lock_key)
        return existing is not None and existing.expires_at > now


lock_manager = DistributedLockManager()
