import pytest
from app.platform.telemetry import PlatformTelemetry


class TestPlatformTelemetry:
    def test_metrics_collection_and_success_rate(self):
        tel = PlatformTelemetry()

        tel.record_task_outcome(success=True, duration_ms=120)
        tel.record_task_outcome(success=True, duration_ms=150)
        tel.record_task_outcome(success=False, duration_ms=200)

        tel.record_tool_call(success=True, duration_ms=15)
        tel.record_tool_call(success=True, duration_ms=25)

        metrics = tel.get_metrics()
        assert metrics["tasks_executed"] == 3
        assert metrics["tasks_succeeded"] == 2
        assert metrics["tasks_failed"] == 1
        assert metrics["task_success_rate"] == 0.667
        assert metrics["tool_success_rate"] == 1.0
        assert metrics["latencies"]["avg_agent_latency_ms"] > 0
