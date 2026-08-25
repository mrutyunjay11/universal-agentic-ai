import pytest
from app.platform.distributed_lock import DistributedLockManager


class TestDistributedLocks:
    def test_mutual_exclusion_and_release(self):
        lm = DistributedLockManager(default_ttl_seconds=10.0)

        # Worker 1 acquires lock
        assert lm.acquire_lock("lock_task_123", "worker_1") is True
        assert lm.is_locked("lock_task_123") is True

        # Worker 2 tries to acquire same lock -> False
        assert lm.acquire_lock("lock_task_123", "worker_2") is False

        # Worker 1 renews lock -> True
        assert lm.renew_lock("lock_task_123", "worker_1") is True

        # Worker 1 releases lock -> True
        assert lm.release_lock("lock_task_123", "worker_1") is True

        # Now Worker 2 can acquire -> True
        assert lm.acquire_lock("lock_task_123", "worker_2") is True
