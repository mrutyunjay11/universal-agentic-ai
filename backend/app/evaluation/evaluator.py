from __future__ import annotations
from typing import Any, Optional
from app.agent.state import AgentState
from app.evaluation.metrics import TaskEvaluationResult, QualityDimension, calibration_tracker
from app.evaluation.rubric import EvaluationRubric, evaluation_rubric
from app.evaluation.task_evaluator import TaskEvaluator, task_evaluator
from app.evaluation.factuality import FactualityEvaluator, factuality_evaluator
from app.evaluation.tool_evaluator import ToolReliabilityMonitor, tool_reliability_monitor
from app.evaluation.planning_evaluator import PlannerEvaluator, planner_evaluator
from app.evaluation.verification_evaluator import VerificationEvaluator, verification_evaluator
from app.evaluation.safety_evaluator import SafetyEvaluator, safety_evaluator
from app.evaluation.reports import RootCauseAnalyzer, root_cause_analyzer, EvaluationReportGenerator, evaluation_reports
from app.evaluation.regression import RegressionSuite, regression_suite
from app.evaluation.benchmarks import BenchmarkFramework, benchmark_framework
from app.evaluation.circuit_breaker import CircuitBreakerManager, circuit_breaker_manager
from app.evaluation.improvement import ControlledSelfImprovementPipeline, self_improvement_pipeline


class UniversalEvaluator:
    """
    Central evaluation coordinator for Phase 4.
    Evaluates complete agent trajectories, tracks reliability, enforces safety gates,
    runs regressions, and manages evidence-based self-improvement.
    """

    def __init__(
        self,
        task_eval: TaskEvaluator | None = None,
        fact_eval: FactualityEvaluator | None = None,
        tool_eval: ToolReliabilityMonitor | None = None,
        plan_eval: PlannerEvaluator | None = None,
        ver_eval: VerificationEvaluator | None = None,
        safe_eval: SafetyEvaluator | None = None,
        rca: RootCauseAnalyzer | None = None,
        reg_suite: RegressionSuite | None = None,
        benchmarks: BenchmarkFramework | None = None,
        breaker_mgr: CircuitBreakerManager | None = None,
        improvement_pipeline: ControlledSelfImprovementPipeline | None = None,
    ):
        self.task_evaluator = task_eval or task_evaluator
        self.factuality_evaluator = fact_eval or factuality_evaluator
        self.tool_monitor = tool_eval or tool_reliability_monitor
        self.planner_evaluator = plan_eval or planner_evaluator
        self.verification_evaluator = ver_eval or verification_evaluator
        self.safety_evaluator = safe_eval or safety_evaluator
        self.root_cause_analyzer = rca or root_cause_analyzer
        self.regression_suite = reg_suite or regression_suite
        self.benchmark_framework = benchmarks or benchmark_framework
        self.circuit_breaker_manager = breaker_mgr or circuit_breaker_manager
        self.self_improvement_pipeline = improvement_pipeline or self_improvement_pipeline
        self.calibration_tracker = calibration_tracker

        self._evaluated_tasks: list[TaskEvaluationResult] = []

    def evaluate(self, state: AgentState) -> TaskEvaluationResult:
        """Evaluates a completed or failed task state and records calibration statistics."""
        result = self.task_evaluator.evaluate_task(state)

        # Run Root Cause Analysis if task failed
        if not result.passed_gate or state.errors:
            rca_res = self.root_cause_analyzer.analyze_failure(state)
            result.failure_category = rca_res.failure_category.value
            result.root_cause = rca_res.root_cause_summary
            result.suggested_improvements = [rca_res.suggested_remediation]

        # Record calibration (predicted confidence vs empirical pass)
        self.calibration_tracker.record_outcome(
            predicted_confidence=state.confidence,
            is_correct=result.passed_gate,
        )

        self._evaluated_tasks.append(result)
        return result

    def get_evaluation(self, task_id: str) -> Optional[TaskEvaluationResult]:
        for res in self._evaluated_tasks:
            if res.task_id == task_id:
                return res
        return None

    def list_evaluations(self, limit: int = 50) -> list[TaskEvaluationResult]:
        return self._evaluated_tasks[-limit:]

    def generate_report(self, run_id: Optional[str] = None) -> dict[str, Any]:
        return evaluation_reports.generate_json_report(self._evaluated_tasks, run_id)

    def generate_markdown_report(self, run_id: Optional[str] = None) -> str:
        return evaluation_reports.generate_markdown_report(self._evaluated_tasks, run_id)


universal_evaluator = UniversalEvaluator()
