from __future__ import annotations
import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ExponentialBackoffRetry:
    """Safe retry handler with exponential backoff and jitter for non-destructive operations."""

    def __init__(self, max_retries: int = 3, base_delay: float = 0.05, max_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(
        self,
        operation_fn: Callable[[], Any],
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> Any:
        attempts = 0
        last_exception = None

        while attempts <= self.max_retries:
            try:
                if asyncio.iscoroutinefunction(operation_fn):
                    return await operation_fn()
                else:
                    return operation_fn()
            except retryable_exceptions as exc:
                last_exception = exc
                attempts += 1
                if attempts > self.max_retries:
                    raise last_exception
                delay = min(self.max_delay, self.base_delay * (2 ** (attempts - 1)))
                await asyncio.sleep(delay)

        raise last_exception or RuntimeError("Retry loop exited unexpectedly")


retry_handler = ExponentialBackoffRetry()
