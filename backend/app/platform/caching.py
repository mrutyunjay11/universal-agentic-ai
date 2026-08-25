from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class CacheEntry(BaseModel):
    key: str
    value: Any
    created_at: float = Field(default_factory=time.time)
    expires_at: float


class PlatformCache:
    """
    Centralized multi-tiered cache with explicit TTLs, secret exclusion,
    and cache hit/miss observability.
    """

    def __init__(self, default_ttl_seconds: float = 300.0):
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        now = time.time()
        if not entry or entry.expires_at < now:
            if entry:
                del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        # Simple safeguard: refuse caching raw credential tokens
        if isinstance(value, str) and ("ghp_" in value or "AKIA" in value or "eyJ" in value):
            return  # Secret exclusion

        ttl = ttl_seconds or self.default_ttl
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=time.time() + ttl,
        )

    def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total) if total > 0 else 0.0
        return {
            "entries_count": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
        }


platform_cache = PlatformCache()
