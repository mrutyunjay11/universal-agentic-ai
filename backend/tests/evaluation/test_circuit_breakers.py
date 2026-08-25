import pytest
import time
from app.evaluation.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerManager


class TestCircuitBreakers:
    def test_circuit_breaker_state_transitions(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_time_seconds=0.1, success_threshold=2)

        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

        # Trigger failures up to threshold
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False

        # Wait for cooldown
        time.sleep(0.12)
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

        # Prove recovery with 2 consecutive successes
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
