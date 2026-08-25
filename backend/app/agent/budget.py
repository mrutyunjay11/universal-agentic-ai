from __future__ import annotations
import time
from typing import Optional
from app.agent.state import BudgetStatus, AgentState


class BudgetManager:
    """Manages iteration, execution time, token, and tool call resource budgets."""

    def __init__(
        self,
        max_iterations: int = 20,
        max_tool_calls: int = 50,
        max_execution_time_seconds: float = 600.0,
        max_tokens: int = 100000,
    ):
        self.default_budget = BudgetStatus(
            max_iterations=max_iterations,
            max_tool_calls=max_tool_calls,
            max_execution_time_seconds=max_execution_time_seconds,
            max_tokens=max_tokens,
        )

    def init_budget(self, state: AgentState):
        state.budget = self.default_budget.model_copy()

    def record_iteration(self, state: AgentState):
        state.iteration_count += 1
        state.budget.current_iterations = state.iteration_count

    def record_elapsed_time(self, state: AgentState, start_time: float):
        state.budget.elapsed_time_seconds = time.time() - start_time

    def record_tokens(self, state: AgentState, token_count: int):
        state.budget.used_tokens += token_count

    def check_budget(self, state: AgentState) -> tuple[bool, Optional[str]]:
        if state.budget.current_iterations >= state.budget.max_iterations:
            return False, f"Iteration budget exceeded ({state.budget.current_iterations}/{state.budget.max_iterations})"
        if state.budget.current_tool_calls >= state.budget.max_tool_calls:
            return False, f"Tool call budget exceeded ({state.budget.current_tool_calls}/{state.budget.max_tool_calls})"
        if state.budget.elapsed_time_seconds >= state.budget.max_execution_time_seconds:
            return False, f"Time budget exceeded ({state.budget.elapsed_time_seconds:.1f}s/{state.budget.max_execution_time_seconds}s)"
        if state.budget.used_tokens >= state.budget.max_tokens:
            return False, f"Token budget exceeded ({state.budget.used_tokens}/{state.budget.max_tokens})"
        return True, None


budget_manager = BudgetManager()
