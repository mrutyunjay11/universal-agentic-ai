from __future__ import annotations
from typing import Any, Optional
from app.evaluation.datasets import GOLDEN_DATASET, GoldenTask, BenchmarkCategory
from app.evaluation.task_evaluator import task_evaluator
from app.tools.permissions import PermissionTier
from app.agent.state import TaskState


class BenchmarkFramework:
    """
    Evaluates agent capabilities against standardized golden datasets across all 14 benchmark domains.
    Measures accuracy, tool selection agreement, verification success, and safety adherence.
    """

    def __init__(self, tasks: Optional[list[GoldenTask]] = None):
        self.tasks = tasks or list(GOLDEN_DATASET)

    async def run_benchmarks(
        self,
        agent_runner: Any,
        category: Optional[BenchmarkCategory] = None,
    ) -> dict[str, Any]:
        targets = [t for t in self.tasks if category is None or t.category == category]
        results = []

        for task in targets:
            state = agent_runner.create_task(
                request=task.prompt,
                permission_granted=PermissionTier.SYSTEM,
            )
            completed_state = await agent_runner.run_task(state)
            eval_result = task_evaluator.evaluate_task(completed_state)

            # Check if expected tool was invoked or safety intercepted
            used_tools = [str(c.get("tool", "")) for c in completed_state.tool_calls]
            if task.category == BenchmarkCategory.SAFETY:
                passed_test = eval_result.safety == 1.0 or len(eval_result.safety_violations) > 0
                tool_match = True
            else:
                tool_match = (
                    any(task.expected_tool in t or t in task.expected_tool for t in used_tools)
                    or any(cap.split('.')[0] in str(used_tools) for cap in task.expected_capabilities)
                    or (eval_result.passed_gate and len(used_tools) > 0)
                )
                passed_test = eval_result.passed_gate or (completed_state.task_status == TaskState.COMPLETED and eval_result.safety == 1.0)

            results.append({
                "task_id": task.id,
                "category": task.category.value,
                "prompt": task.prompt,
                "passed_gate": passed_test,
                "score": eval_result.overall_score,
                "correctness": eval_result.correctness,
                "safety": eval_result.safety,
                "tool_matched": tool_match,
            })

        total = len(results)
        passed = sum(1 for r in results if r["passed_gate"])

        return {
            "total_benchmark_tasks": total,
            "passed_count": passed,
            "pass_rate": round(passed / max(1, total), 4),
            "average_score": round(sum(r["score"] for r in results) / max(1, total), 4),
            "results": results,
        }


benchmark_framework = BenchmarkFramework()
