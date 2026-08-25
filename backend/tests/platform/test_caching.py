import pytest
import time
from app.platform.caching import PlatformCache


class TestPlatformCaching:
    def test_cache_ttl_and_secret_exclusion(self):
        cache = PlatformCache(default_ttl_seconds=0.1)

        # Set and get
        cache.set("query_embeddings_abc", [0.12, 0.45, 0.78])
        assert cache.get("query_embeddings_abc") == [0.12, 0.45, 0.78]

        # Secret exclusion check
        cache.set("token_key", "ghp_super_secret_pat_998")
        assert cache.get("token_key") is None  # Should be rejected from cache

        # Expiration
        time.sleep(0.15)
        assert cache.get("query_embeddings_abc") is None
