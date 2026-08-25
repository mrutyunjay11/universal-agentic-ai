import pytest
from app.context.benchmarks import ContextBenchmarkSuite


class TestContextBenchmarks:
    def test_benchmark_comparison_run(self):
        suite = ContextBenchmarkSuite()
        results = suite.run_comparison(
            task="Evaluate framework compatibility across major versions",
            corpus_size_docs=50,
        )

        assert len(results) == 5
        strategies = [r.strategy for r in results]
        assert "FULL_CONTEXT" in strategies
        assert "DYNAMIC_CONTEXT" in strategies
        assert "DYNAMIC_CONTEXT_VERIFIED" in strategies

        # DYNAMIC_CONTEXT should consume significantly fewer tokens than FULL_CONTEXT
        full = next(r for r in results if r.strategy == "FULL_CONTEXT")
        dyn = next(r for r in results if r.strategy == "DYNAMIC_CONTEXT")
        assert dyn.token_count < full.token_count
        assert dyn.accuracy_score > full.accuracy_score
