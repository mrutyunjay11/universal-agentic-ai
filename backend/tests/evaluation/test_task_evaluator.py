import pytest
from app.evaluation.task_evaluator import TaskEvaluator
from app.agent.state import AgentState, TaskState, Plan, PlanStep, StepStatus, StructuredObservation, VerificationVerdict


class TestTaskEvaluator:
    def test_evaluate_successful_task(self):
        evaluator = TaskEvaluator()
        state = AgentState(
            original_request="Inspect code repository",
            normalized_goal="Inspect code repository",
            task_status=TaskState.COMPLETED,
            confidence=0.95,
        )
        state.plan = Plan(
            plan_id="p1",
            goal="Inspect code",
            steps=[PlanStep(id="s1", description="List files", objective="Scan dir", tool_name="list_directory", status=StepStatus.COMPLETED)],
        )
        state.observations.append(StructuredObservation(
            step_id="s1",
            tool_name="list_directory",
            success=True,
            summary="Found 15 python files in backend",
            evidence=[{"uri": "file:///workspace", "snippet": "Found 15 python files"}],
        ))
        state.verification_results.append(VerificationVerdict(
            step_id="s1",
            claim="Found python files",
            status="verified",
            confidence=0.95,
            evidence_ids=["file:///workspace"],
            details={},
        ))
        state.final_result = {"summary": "Completed code inspection. Found 15 python files in backend."}

        res = evaluator.evaluate_task(state)
        assert res.correctness >= 0.85
        assert res.safety == 1.0
        assert res.passed_gate is True
        assert res.overall_score >= 0.80

    def test_evaluate_failed_task(self):
        evaluator = TaskEvaluator()
        state = AgentState(
            original_request="Failing task test",
            task_status=TaskState.FAILED,
            confidence=0.3,
            errors=[{"error": "Tool execution failed"}],
        )
        res = evaluator.evaluate_task(state)
        assert res.passed_gate is False
        assert res.completeness == 0.0
