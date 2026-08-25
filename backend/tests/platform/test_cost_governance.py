import pytest
from app.platform.cost_governance import CostGovernanceManager


class TestCostGovernance:
    def test_cost_accounting_and_budget_limits(self):
        cg = CostGovernanceManager()
        cg.set_budget("user_bob", max_budget_usd=0.05)

        # 1st expense: 10,000 tokens ($0.02) -> OK
        ok1, _, rec1 = cg.record_expense("task_1", user_id="user_bob", llm_tokens=10000)
        assert ok1 is True
        assert rec1.llm_cost_usd == 0.02

        # 2nd expense: 20,000 tokens ($0.04) -> Total $0.06 > Budget $0.05 -> Exceeded
        ok2, msg2, _ = cg.record_expense("task_2", user_id="user_bob", llm_tokens=20000)
        assert ok2 is False
        assert "Budget limit of $0.05 exceeded" in msg2
