from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.agent.state import AgentState, TaskState, StepStatus
from app.evaluation.metrics import TaskEvaluationResult


class FailureTaxonomy(str, Enum):
    MODEL_ERROR = "MODEL_ERROR"
    PLANNING_ERROR = "PLANNING_ERROR"
    ROUTING_ERROR = "ROUTING_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    TOOL_OUTPUT_ERROR = "TOOL_OUTPUT_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    CONTEXT_ERROR = "CONTEXT_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    USER_REQUIREMENT_ERROR = "USER_REQUIREMENT_ERROR"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


class RootCauseAnalysisResult(BaseModel):
    task_id: str
    failure_category: FailureTaxonomy = FailureTaxonomy.UNKNOWN
    root_cause_summary: str
    first_abnormal_step: Optional[str] = None
    contributing_factors: list[str] = Field(default_factory=list)
    suggested_remediation: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RootCauseAnalyzer:
    """
    Analyzes failed or degraded agent execution trajectories to identify the earliest
    abnormal event and map the failure into the 16-category standardized taxonomy.
    """

    def analyze_failure(self, state: AgentState) -> RootCauseAnalysisResult:
        if state.task_status == TaskState.COMPLETED and not state.errors:
            return RootCauseAnalysisResult(
                task_id=state.task_id,
                failure_category=FailureTaxonomy.UNKNOWN,
                root_cause_summary="No failure detected; task completed cleanly",
                suggested_remediation="None required",
            )

        # 1. Check budget exhaustion / timeouts
        if state.budget and state.budget.is_exhausted:
            return RootCauseAnalysisResult(
                task_id=state.task_id,
                failure_category=FailureTaxonomy.RESOURCE_LIMIT,
                root_cause_summary=f"Iteration/tool resource budget exhausted ({state.budget.current_iterations} iters, {state.budget.current_tool_calls} tool calls)",
                contributing_factors=["Plan required more iterations than allotted budget quota"],
                suggested_remediation="Refine planner step decomposition or increase task iteration budget",
            )

        # 2. Check tool failures in plan steps
        if state.plan and state.plan.steps:
            for s in state.plan.steps:
                if s.status == StepStatus.FAILED or s.error:
                    err_str = str(s.error).lower()
                    if "permission" in err_str:
                        return RootCauseAnalysisResult(
                            task_id=state.task_id,
                            failure_category=FailureTaxonomy.PERMISSION_ERROR,
                            root_cause_summary=f"Tool '{s.tool_name}' was blocked due to insufficient permissions",
                            first_abnormal_step=s.id,
                            contributing_factors=[f"Execution required elevated permission tier: {s.error}"],
                            suggested_remediation="Request user approval or elevate execution permission tier",
                        )
                    elif "timeout" in err_str:
                        return RootCauseAnalysisResult(
                            task_id=state.task_id,
                            failure_category=FailureTaxonomy.TIMEOUT,
                            root_cause_summary=f"Tool '{s.tool_name}' timed out during execution",
                            first_abnormal_step=s.id,
                            contributing_factors=["External network or execution latency"],
                            suggested_remediation="Increase tool timeout limits or check service availability",
                        )
                    else:
                        return RootCauseAnalysisResult(
                            task_id=state.task_id,
                            failure_category=FailureTaxonomy.TOOL_ERROR,
                            root_cause_summary=f"Tool '{s.tool_name}' failed with error: {s.error}",
                            first_abnormal_step=s.id,
                            contributing_factors=["Invalid arguments, missing dependencies, or runtime tool crash"],
                            suggested_remediation="Inspect tool inputs or use alternative capability fallback",
                        )

        # 3. Check verification contradictions
        refuted_verifications = [v for v in state.verification_results if v.status in ("refuted", "contradicted")]
        if refuted_verifications:
            return RootCauseAnalysisResult(
                task_id=state.task_id,
                failure_category=FailureTaxonomy.VERIFICATION_ERROR,
                root_cause_summary=f"Claim '{refuted_verifications[0].claim}' was refuted during empirical verification",
                contributing_factors=["Calculated or extracted result contradicted claimed output"],
                suggested_remediation="Re-evaluate calculation/code implementation before asserting final conclusion",
            )

        # 4. Check explicit error list
        if state.errors:
            err_msg = str(state.errors[0])
            return RootCauseAnalysisResult(
                task_id=state.task_id,
                failure_category=FailureTaxonomy.PLANNING_ERROR,
                root_cause_summary=f"Agent orchestration encountered error: {err_msg[:120]}",
                contributing_factors=[err_msg],
                suggested_remediation="Verify task understanding and plan validation constraints",
            )

        return RootCauseAnalysisResult(
            task_id=state.task_id,
            failure_category=FailureTaxonomy.UNKNOWN,
            root_cause_summary="Generic task failure",
            suggested_remediation="Review trajectory logs",
        )


class EvaluationReportGenerator:
    """Generates machine-readable (JSON) and human-readable (Markdown) evaluation reports."""

    @staticmethod
    def generate_json_report(eval_results: list[TaskEvaluationResult], run_id: Optional[str] = None) -> dict[str, Any]:
        total = len(eval_results)
        if total == 0:
            return {"run_id": run_id or f"run_{uuid.uuid4().hex[:8]}", "total_tasks": 0}

        passed = sum(1 for e in eval_results if e.passed_gate)
        avg_score = sum(e.overall_score for e in eval_results) / total
        avg_correctness = sum(e.correctness for e in eval_results) / total
        avg_safety = sum(e.safety for e in eval_results) / total
        avg_evidence = sum(e.evidence_quality for e in eval_results) / total
        avg_ver = sum(e.verification_quality for e in eval_results) / total
        safety_failures = sum(len(e.safety_violations) for e in eval_results)

        return {
            "run_id": run_id or f"run_{uuid.uuid4().hex[:8]}",
            "total_tasks": total,
            "passed_gate_count": passed,
            "pass_rate": round(passed / total, 4),
            "average_overall_score": round(avg_score, 4),
            "average_correctness": round(avg_correctness, 4),
            "average_safety": round(avg_safety, 4),
            "average_evidence_quality": round(avg_evidence, 4),
            "average_verification_quality": round(avg_ver, 4),
            "total_safety_failures": safety_failures,
            "tasks": [e.to_dict() for e in eval_results],
        }

    @staticmethod
    def generate_markdown_report(eval_results: list[TaskEvaluationResult], run_id: Optional[str] = None) -> str:
        data = EvaluationReportGenerator.generate_json_report(eval_results, run_id)
        if data.get("total_tasks", 0) == 0:
            return "# Evaluation Report\n\nNo tasks evaluated."

        md = f"""# Evaluation Run Report: `{data['run_id']}`

## Executive Summary
- **Total Tasks Evaluated**: {data['total_tasks']}
- **Pass Rate**: {data['pass_rate'] * 100:.1f}% ({data['passed_gate_count']}/{data['total_tasks']})
- **Average Overall Score**: {data['average_overall_score']:.3f}
- **Average Correctness**: {data['average_correctness']:.3f}
- **Safety Score**: {data['average_safety']:.3f} (Violations: {data['total_safety_failures']})
- **Evidence Quality**: {data['average_evidence_quality']:.3f}
- **Verification Quality**: {data['average_verification_quality']:.3f}

---

## Detailed Task Breakdown
| Task ID | Goal | Correctness | Safety | Evidence | Overall | Gate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for t in data["tasks"][:20]:
            goal = (t["original_request"][:40] + "...") if len(t["original_request"]) > 40 else t["original_request"]
            gate_str = "✅ PASS" if t["passed_gate"] else "❌ FAIL"
            md += f"| `{t['task_id']}` | {goal} | {t['correctness']:.2f} | {t['safety']:.2f} | {t['evidence_quality']:.2f} | **{t['overall_score']:.2f}** | {gate_str} |\n"

        return md


root_cause_analyzer = RootCauseAnalyzer()
evaluation_reports = EvaluationReportGenerator()
