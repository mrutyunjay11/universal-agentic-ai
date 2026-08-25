from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class PlatformTelemetry:
    """
    Collects performance, latency, throughput, and error metrics across all platform layers.
    """

    def __init__(self):
        self.tasks_executed = 0
        self.tasks_succeeded = 0
        self.tasks_failed = 0
        self.tool_calls_total = 0
        self.tool_calls_succeeded = 0
        self.latencies_ms: dict[str, list[int]] = {
            "agent": [],
            "tool": [],
            "llm": [],
            "queue": [],
            "memory_retrieval": [],
        }

    def record_task_outcome(self, success: bool, duration_ms: int) -> None:
        self.tasks_executed += 1
        if success:
            self.tasks_succeeded += 1
        else:
            self.tasks_failed += 1
        self.latencies_ms["agent"].append(duration_ms)

    def record_tool_call(self, success: bool, duration_ms: int) -> None:
        self.tool_calls_total += 1
        if success:
            self.tool_calls_succeeded += 1
        self.latencies_ms["tool"].append(duration_ms)

    def record_latency(self, metric_name: str, duration_ms: int) -> None:
        if metric_name in self.latencies_ms:
            self.latencies_ms[metric_name].append(duration_ms)

    def get_metrics(self) -> dict[str, Any]:
        task_success_rate = (self.tasks_succeeded / self.tasks_executed) if self.tasks_executed > 0 else 1.0
        tool_success_rate = (self.tool_calls_succeeded / self.tool_calls_total) if self.tool_calls_total > 0 else 1.0

        avg_latencies = {}
        for k, v in self.latencies_ms.items():
            avg_latencies[f"avg_{k}_latency_ms"] = round(sum(v) / len(v), 1) if v else 0.0

        return {
            "tasks_executed": self.tasks_executed,
            "tasks_succeeded": self.tasks_succeeded,
            "tasks_failed": self.tasks_failed,
            "task_success_rate": round(task_success_rate, 3),
            "tool_calls_total": self.tool_calls_total,
            "tool_success_rate": round(tool_success_rate, 3),
            "latencies": avg_latencies,
        }


telemetry = PlatformTelemetry()
