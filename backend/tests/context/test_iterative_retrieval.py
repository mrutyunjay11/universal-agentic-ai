import pytest
from app.context.planner import ContextPlanner
from app.context.evidence import RequirementCoverageReport
from app.context.iterative_retrieval import IterativeRetrievalEngine
from app.context.sufficiency import SufficiencyEvaluationResult
from app.context.policies import ContextSufficiencyStatus


class TestIterativeRetrieval:
    def test_diminishing_returns_and_max_iterations_halt(self):
        engine = IterativeRetrievalEngine(max_iterations=3, min_progress_delta=0.05)

        suff_insufficient = SufficiencyEvaluationResult(
            status=ContextSufficiencyStatus.INSUFFICIENT,
            coverage_score=0.6,
            is_sufficient=False,
        )

        # Iteration 1 -> Continue
        cont1, _ = engine.should_continue_retrieval(1, 0.0, 0.6, suff_insufficient)
        assert cont1 is True

        # Iteration 2 with minor gain (delta=0.01 < 0.05) -> Halt due to diminishing returns
        cont2, msg2 = engine.should_continue_retrieval(2, 0.60, 0.61, suff_insufficient)
        assert cont2 is False
        assert "Diminishing returns" in msg2

        # Max iteration reached -> Halt
        cont3, msg3 = engine.should_continue_retrieval(3, 0.60, 0.75, suff_insufficient)
        assert cont3 is False
        assert "Maximum retrieval iterations" in msg3
