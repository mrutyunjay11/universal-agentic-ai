import pytest
from app.evaluation.benchmarks import BenchmarkFramework
from app.evaluation.datasets import GoldenTask, BenchmarkCategory
from app.agent.agent import universal_agent


class TestBenchmarkFramework:
    @pytest.mark.asyncio
    async def test_run_math_benchmark(self):
        math_task = GoldenTask(
            id="gold_math_test",
            category=BenchmarkCategory.MATH,
            prompt="Calculate (50 * 4) + sqrt(144)",
            expected_capabilities=["math.calculate"],
            expected_tool="calculator",
            verification_condition="result == 212.0",
            ground_truth_answer="212.0",
        )

        framework = BenchmarkFramework(tasks=[math_task])
        res = await framework.run_benchmarks(universal_agent)

        assert res["total_benchmark_tasks"] == 1
        assert res["passed_count"] == 1
        assert res["pass_rate"] == 1.0
        assert res["results"][0]["tool_matched"] is True
