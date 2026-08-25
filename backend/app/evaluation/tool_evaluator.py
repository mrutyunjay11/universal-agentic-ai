from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolMetricRecord(BaseModel):
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    permission_denials: int = 0
    invalid_input_calls: int = 0
    total_latency_ms: int = 0

    @property
    def success_rate(self) -> float:
        return (self.successful_calls / self.total_calls) if self.total_calls > 0 else 1.0

    @property
    def average_latency_ms(self) -> float:
        return (self.total_latency_ms / self.total_calls) if self.total_calls > 0 else 0.0

    @property
    def reliability_score(self) -> float:
        """Composite health score [0.0 - 1.0]."""
        if self.total_calls == 0:
            return 1.0
        penalty = (self.failed_calls * 1.0 + self.timeout_calls * 1.5 + self.permission_denials * 0.5) / self.total_calls
        return max(0.0, min(1.0, 1.0 - penalty))


class ToolReliabilityMonitor:
    """
    Monitors execution metrics across all tools.
    Provides diagnostic statistics and reliability signals to aid capability-based routing.
    """

    def __init__(self):
        self._metrics: dict[str, ToolMetricRecord] = {}

    def record_call(
        self,
        tool_name: str,
        success: bool,
        duration_ms: int,
        error_type: Optional[str] = None,
    ) -> None:
        if tool_name not in self._metrics:
            self._metrics[tool_name] = ToolMetricRecord(tool_name=tool_name)

        m = self._metrics[tool_name]
        m.total_calls += 1
        m.total_latency_ms += duration_ms

        if success:
            m.successful_calls += 1
        else:
            m.failed_calls += 1
            if error_type == "TIMEOUT":
                m.timeout_calls += 1
            elif error_type == "PERMISSION_DENIED":
                m.permission_denials += 1
            elif error_type == "VALIDATION_ERROR":
                m.invalid_input_calls += 1

    def get_tool_metrics(self, tool_name: str) -> Optional[ToolMetricRecord]:
        return self._metrics.get(tool_name)

    def get_all_metrics(self) -> list[dict[str, Any]]:
        return [
            {
                "tool_name": m.tool_name,
                "total_calls": m.total_calls,
                "success_rate": round(m.success_rate, 4),
                "average_latency_ms": round(m.average_latency_ms, 2),
                "reliability_score": round(m.reliability_score, 4),
                "failed_calls": m.failed_calls,
                "timeout_calls": m.timeout_calls,
            }
            for m in self._metrics.values()
        ]

    def clear(self) -> None:
        self._metrics.clear()


tool_reliability_monitor = ToolReliabilityMonitor()
