from __future__ import annotations
import time
from enum import Enum
from typing import Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal execution
    OPEN = "OPEN"          # Tripped; requests rejected
    HALF_OPEN = "HALF_OPEN"# Testing recovery with limited traffic


class CircuitBreaker:
    """
    Circuit breaker protecting against repeated failures and retry storms on external tools/services.
    Enforces failure thresholds, cooldown timers, and recovery probes.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_time_seconds: float = 30.0,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.success_threshold = success_threshold

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float = 0.0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_time_seconds:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        return True

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN


class CircuitBreakerManager:
    """Manages circuit breakers for individual tools and external endpoints."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(self, resource_name: str) -> CircuitBreaker:
        if resource_name not in self._breakers:
            self._breakers[resource_name] = CircuitBreaker()
        return self._breakers[resource_name]

    def can_execute(self, resource_name: str) -> bool:
        return self.get_breaker(resource_name).can_execute()

    def record_success(self, resource_name: str) -> None:
        self.get_breaker(resource_name).record_success()

    def record_failure(self, resource_name: str) -> None:
        self.get_breaker(resource_name).record_failure()


circuit_breaker_manager = CircuitBreakerManager()
