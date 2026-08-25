from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskResourceBudget(BaseModel):
    task_id: str
    max_execution_seconds: float = 300.0
    max_llm_tokens: int = 100000
    max_tool_calls: int = 50
    max_external_api_calls: int = 25
    used_execution_seconds: float = 0.0
    used_llm_tokens: int = 0
    used_tool_calls: int = 0
    used_external_api_calls: int = 0
    start_time: float = Field(default_factory=time.time)


class ResourceLimiter:
    """
    Enforces deterministic resource boundaries on tasks independently from model instructions.
    Prevents runaway loops, token bloat, or memory leaks.
    """

    def __init__(self):
        self._budgets: dict[str, TaskResourceBudget] = {}

    def initialize_task(
        self,
        task_id: str,
        max_execution_seconds: float = 300.0,
        max_llm_tokens: int = 100000,
        max_tool_calls: int = 50,
    ) -> TaskResourceBudget:
        budget = TaskResourceBudget(
            task_id=task_id,
            max_execution_seconds=max_execution_seconds,
            max_llm_tokens=max_llm_tokens,
            max_tool_calls=max_tool_calls,
        )
        self._budgets[task_id] = budget
        return budget

    def record_usage(
        self,
        task_id: str,
        tokens: int = 0,
        tool_calls: int = 0,
        api_calls: int = 0,
    ) -> tuple[bool, str]:
        budget = self._budgets.get(task_id)
        if not budget:
            budget = self.initialize_task(task_id)

        budget.used_llm_tokens += tokens
        budget.used_tool_calls += tool_calls
        budget.used_external_api_calls += api_calls
        budget.used_execution_seconds = time.time() - budget.start_time

        # Check limit violations
        if budget.used_execution_seconds > budget.max_execution_seconds:
            return False, f"Execution time limit exceeded ({budget.used_execution_seconds:.1f}s > {budget.max_execution_seconds}s)"

        if budget.used_llm_tokens > budget.max_llm_tokens:
            return False, f"Token budget exceeded ({budget.used_llm_tokens} > {budget.max_llm_tokens})"

        if budget.used_tool_calls > budget.max_tool_calls:
            return False, f"Tool call budget exceeded ({budget.used_tool_calls} > {budget.max_tool_calls})"

        return True, "Within limits"

    def get_budget(self, task_id: str) -> Optional[TaskResourceBudget]:
        return self._budgets.get(task_id)


resource_limiter = ResourceLimiter()
