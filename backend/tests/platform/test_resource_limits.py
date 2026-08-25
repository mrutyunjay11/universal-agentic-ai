import pytest
from app.platform.resource_limiter import ResourceLimiter


class TestResourceLimits:
    def test_token_and_tool_call_limit_enforcement(self):
        limiter = ResourceLimiter()
        limiter.initialize_task("task_test_limits", max_llm_tokens=1000, max_tool_calls=5)

        # Within bounds
        ok, _ = limiter.record_usage("task_test_limits", tokens=500, tool_calls=2)
        assert ok is True

        # Exceeding tool calls
        exceeded, msg = limiter.record_usage("task_test_limits", tokens=200, tool_calls=4)
        assert exceeded is False
        assert "Tool call budget exceeded" in msg
