from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class CostRecord(BaseModel):
    task_id: str
    user_id: str = "default_user"
    project_id: Optional[str] = None
    llm_cost_usd: float = 0.0
    gpu_cost_usd: float = 0.0
    cloud_cost_usd: float = 0.0
    tool_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class BudgetLimit(BaseModel):
    entity_id: str  # user_id or project_id or task_id
    max_budget_usd: float = 10.0
    current_spend_usd: float = 0.0
    warning_threshold_pct: float = 80.0


class CostGovernanceManager:
    """
    Tracks and accounts for all operational costs across LLM inference tokens,
    GPU hours, cloud infrastructure, and external API requests. Enforces strict budget caps.
    """

    def __init__(self):
        self._records: list[CostRecord] = []
        self._budgets: dict[str, BudgetLimit] = {}

    def set_budget(self, entity_id: str, max_budget_usd: float) -> BudgetLimit:
        budget = BudgetLimit(entity_id=entity_id, max_budget_usd=max_budget_usd)
        self._budgets[entity_id] = budget
        return budget

    def record_expense(
        self,
        task_id: str,
        user_id: str = "default_user",
        project_id: Optional[str] = None,
        llm_tokens: int = 0,
        gpu_seconds: float = 0.0,
        tool_calls: int = 0,
    ) -> tuple[bool, str, CostRecord]:
        # Unit costs: $0.000002 / token, $0.0008 / GPU second, $0.001 / tool call
        llm_cost = llm_tokens * 0.000002
        gpu_cost = gpu_seconds * 0.0008
        tool_cost = tool_calls * 0.001
        total = llm_cost + gpu_cost + tool_cost

        rec = CostRecord(
            task_id=task_id,
            user_id=user_id,
            project_id=project_id,
            llm_cost_usd=llm_cost,
            gpu_cost_usd=gpu_cost,
            tool_cost_usd=tool_cost,
            total_cost_usd=total,
        )
        self._records.append(rec)

        # Check budgets for user and project
        for eid in [user_id, project_id, task_id]:
            if eid and eid in self._budgets:
                b = self._budgets[eid]
                b.current_spend_usd += total
                if b.current_spend_usd > b.max_budget_usd:
                    return False, f"Budget limit of ${b.max_budget_usd:.2f} exceeded for {eid} (current spend: ${b.current_spend_usd:.2f})", rec
                elif (b.current_spend_usd / b.max_budget_usd) * 100 >= b.warning_threshold_pct:
                    # Warning threshold reached
                    pass

        return True, "Cost recorded within budget", rec

    def get_total_spend_for_user(self, user_id: str) -> float:
        return sum(r.total_cost_usd for r in self._records if r.user_id == user_id)

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_expenses_count": len(self._records),
            "total_spend_usd": round(sum(r.total_cost_usd for r in self._records), 4),
            "llm_spend_usd": round(sum(r.llm_cost_usd for r in self._records), 4),
            "gpu_spend_usd": round(sum(r.gpu_cost_usd for r in self._records), 4),
            "tool_spend_usd": round(sum(r.tool_cost_usd for r in self._records), 4),
        }


cost_governance = CostGovernanceManager()
