from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class RateLimitQuota(BaseModel):
    provider: str
    max_requests_per_minute: int = 60
    current_tokens: float = 60.0
    last_refill_time: float = Field(default_factory=time.time)


class RateLimitManager:
    """Token-bucket rate limiter per integration provider to prevent API quotas depletion."""

    def __init__(self):
        self._quotas: dict[str, RateLimitQuota] = {}

    def configure_provider(self, provider: str, max_requests_per_minute: int = 60) -> None:
        self._quotas[provider] = RateLimitQuota(
            provider=provider,
            max_requests_per_minute=max_requests_per_minute,
            current_tokens=float(max_requests_per_minute),
            last_refill_time=time.time(),
        )

    def check_and_consume(self, provider: str, cost: float = 1.0) -> bool:
        if provider not in self._quotas:
            self.configure_provider(provider, 60)

        quota = self._quotas[provider]
        now = time.time()
        elapsed = now - quota.last_refill_time
        # Refill tokens
        refill_rate = quota.max_requests_per_minute / 60.0
        quota.current_tokens = min(float(quota.max_requests_per_minute), quota.current_tokens + (elapsed * refill_rate))
        quota.last_refill_time = now

        if quota.current_tokens >= cost:
            quota.current_tokens -= cost
            return True
        return False


rate_limit_manager = RateLimitManager()
