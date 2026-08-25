from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class ResourceUsageRecord(BaseModel):
    task_id: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tool_calls: int = 0
    total_execution_time_ms: int = 0
    estimated_cost_usd: float = 0.0
    agent_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ResourceManager:
    """
    Centralized resource accounting and budget enforcement.
    Tracks token consumption, tool calls, execution latency, and cost per task and agent.
    """

    def __init__(self):
        self._records: dict[str, ResourceUsageRecord] = {}

    def get_or_create_record(self, task_id: str) -> ResourceUsageRecord:
        if task_id not in self._records:
            self._records[task_id] = ResourceUsageRecord(task_id=task_id)
        return self._records[task_id]

    def record_usage(
        self,
        task_id: str,
        agent_name: str,
        tokens: int = 0,
        tool_calls: int = 0,
        duration_ms: int = 0,
    ) -> None:
        rec = self.get_or_create_record(task_id)
        rec.total_tokens += tokens
        rec.total_tool_calls += tool_calls
        rec.total_execution_time_ms += duration_ms
        # Approximate cost calculation ($0.002 / 1k tokens)
        rec.estimated_cost_usd += (tokens / 1000.0) * 0.002

        if agent_name not in rec.agent_breakdown:
            rec.agent_breakdown[agent_name] = {
                "tokens": 0,
                "tool_calls": 0,
                "duration_ms": 0,
            }
        rec.agent_breakdown[agent_name]["tokens"] += tokens
        rec.agent_breakdown[agent_name]["tool_calls"] += tool_calls
        rec.agent_breakdown[agent_name]["duration_ms"] += duration_ms

    def get_task_usage(self, task_id: str) -> ResourceUsageRecord:
        return self.get_or_create_record(task_id)


resource_manager = ResourceManager()
