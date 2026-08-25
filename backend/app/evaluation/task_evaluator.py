from __future__ import annotations
from typing import Any
from app.agent.state import AgentState, TaskState, StepStatus
from app.evaluation.metrics import TaskEvaluationResult, CriterionEvaluation, CriterionStatus, QualityDimension
from app.evaluation.rubric import EvaluationRubric, evaluation_rubric
from app.evaluation.factuality import FactualityEvaluator, factuality_evaluator
from app.evaluation.planning_evaluator import PlannerEvaluator, planner_evaluator
from app.evaluation.verification_evaluator import VerificationEvaluator, verification_evaluator
from app.evaluation.safety_evaluator import SafetyEvaluator, safety_evaluator


class TaskEvaluator:
    """
    Evaluates complete agent execution trajectories across all 8 quality dimensions:
    CORRECTNESS, COMPLETENESS, RELEVANCE, EVIDENCE_QUALITY, VERIFICATION_QUALITY,
    SAFETY, EFFICIENCY, and REPRODUCIBILITY.
    """

    def __init__(
        self,
        rubric: EvaluationRubric | None = None,
        fact_eval: FactualityEvaluator | None = None,
        plan_eval: PlannerEvaluator | None = None,
        ver_eval: VerificationEvaluator | None = None,
        safe_eval: SafetyEvaluator | None = None,
    ):
        self.rubric = rubric or evaluation_rubric
        self.fact_eval = fact_eval or factuality_evaluator
        self.plan_eval = plan_eval or planner_evaluator
        self.ver_eval = ver_eval or verification_evaluator
        self.safe_eval = safe_eval or safety_evaluator

    def evaluate_task(self, state: AgentState) -> TaskEvaluationResult:
        # 1. Evaluate Safety
        safety_res = self.safe_eval.evaluate_safety(state)
        safety_score = safety_res["safety_score"]

        # 2. Evaluate Factuality & Evidence
        fact_res = self.fact_eval.evaluate_factuality(state)
        evidence_score = fact_res["factuality_score"]

        # 3. Evaluate Verification
        ver_res = self.ver_eval.evaluate_verifications(state)
        verification_score = ver_res["score"]

        # 4. Evaluate Plan Quality
        plan_res = self.plan_eval.evaluate_plan(state.plan)

        # 5. Evaluate Completeness & Requirements
        criteria_results: list[CriterionEvaluation] = []
        completeness_score = 1.0

        if state.plan and state.plan.steps:
            completed_steps = [s for s in state.plan.steps if s.status == StepStatus.COMPLETED]
            completeness_score = len(completed_steps) / len(state.plan.steps)
        elif state.task_status != TaskState.COMPLETED:
            completeness_score = 0.0

        # Evaluate explicit success criteria
        understanding = state.context.get("understanding", {}) if isinstance(state.context, dict) else {}
        criteria = understanding.get("success_criteria") or getattr(state, "success_criteria", None) or ["Fulfill user request"]

        pass_count = 0
        for crit in criteria:
            is_met = state.task_status == TaskState.COMPLETED and not state.errors
            crit_status = CriterionStatus.PASS if is_met else CriterionStatus.FAIL
            crit_score = 1.0 if is_met else 0.0
            if is_met:
                pass_count += 1

            criteria_results.append(CriterionEvaluation(
                criterion=crit,
                status=crit_status,
                score=crit_score,
                reasoning=f"Task ended with state {state.task_status.value}",
            ))

        # 6. Correctness & Relevance
        correctness_base = 1.0 if state.task_status == TaskState.COMPLETED else 0.4
        if state.errors:
            correctness_base = max(0.0, correctness_base - len(state.errors) * 0.2)
        correctness_score = round(min(1.0, (correctness_base * 2.0 + evidence_score + verification_score) / 4.0), 4)
        if state.task_status == TaskState.COMPLETED and not state.errors:
            correctness_score = max(correctness_score, 0.85)

        relevance_score = 1.0 if state.normalized_goal else 0.8

        # 7. Efficiency Score
        efficiency_score = 1.0
        if state.budget:
            it_ratio = state.budget.current_iterations / max(1, state.budget.max_iterations)
            efficiency_score = max(0.2, 1.0 - (it_ratio * 0.5))

        reproducibility_score = 0.95 if state.plan and not plan_res["issues"] else 0.70

        # 8. Composite Score & Gate Evaluation
        overall_score = self.rubric.compute_composite_score(
            correctness=correctness_score,
            completeness=completeness_score,
            relevance=relevance_score,
            evidence_quality=evidence_score,
            verification_quality=verification_score,
            safety=safety_score,
            efficiency=efficiency_score,
            reproducibility=reproducibility_score,
        )

        passed_gate = self.rubric.evaluate_gate(
            composite_score=overall_score,
            correctness=correctness_score,
            safety=safety_score,
            evidence_quality=evidence_score,
            verification_quality=verification_score,
        )

        duration_ms = int(sum(s.duration_ms for s in state.plan.steps)) if state.plan else 0

        return TaskEvaluationResult(
            task_id=state.task_id,
            original_request=state.original_request,
            correctness=correctness_score,
            completeness=round(completeness_score, 4),
            relevance=round(relevance_score, 4),
            evidence_quality=round(evidence_score, 4),
            verification_quality=round(verification_score, 4),
            safety=round(safety_score, 4),
            efficiency=round(efficiency_score, 4),
            reproducibility=round(reproducibility_score, 4),
            overall_score=round(overall_score, 4),
            passed_gate=passed_gate,
            criteria_results=criteria_results,
            safety_violations=safety_res["violations"],
            total_tool_calls=len(state.tool_calls),
            execution_duration_ms=duration_ms,
            metadata={
                "task_status": state.task_status.value,
                "plan_eval": plan_res,
                "factuality_eval": fact_res,
                "verification_eval": ver_res,
            },
        )


task_evaluator = TaskEvaluator()
