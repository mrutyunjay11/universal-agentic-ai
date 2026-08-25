import pytest
from app.context.planner import ContextPlanner
from app.context.query_expansion import QueryDecomposer


class TestQueryExpansion:
    def test_query_decomposition_guardrails(self):
        planner = ContextPlanner()
        decomposer = QueryDecomposer(max_subqueries=3)

        plan = planner.create_context_plan("Verify compatibility of PyTorch with CUDA 12.4 on Linux")
        subqueries = decomposer.decompose(plan)

        assert len(subqueries) <= 3
        assert all(len(sq.query_text) > 0 for sq in subqueries)
        assert len(set(sq.query_text for sq in subqueries)) == len(subqueries)
