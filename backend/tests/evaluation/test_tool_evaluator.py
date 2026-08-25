import pytest
from app.evaluation.tool_evaluator import ToolReliabilityMonitor


class TestToolEvaluator:
    def test_tool_metrics_recording_and_health(self):
        monitor = ToolReliabilityMonitor()

        # Record 4 successes and 1 failure
        monitor.record_call("search_web", success=True, duration_ms=200)
        monitor.record_call("search_web", success=True, duration_ms=300)
        monitor.record_call("search_web", success=True, duration_ms=250)
        monitor.record_call("search_web", success=True, duration_ms=250)
        monitor.record_call("search_web", success=False, duration_ms=500, error_type="TIMEOUT")

        metrics = monitor.get_tool_metrics("search_web")
        assert metrics is not None
        assert metrics.total_calls == 5
        assert metrics.successful_calls == 4
        assert metrics.failed_calls == 1
        assert metrics.timeout_calls == 1
        assert metrics.success_rate == 0.80
        assert metrics.average_latency_ms == 300.0
        assert metrics.reliability_score < 1.0
