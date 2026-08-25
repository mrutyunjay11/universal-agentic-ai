from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.evaluation.evaluator import universal_evaluator
from app.evaluation.improvement import ImprovementType
from app.agent.agent import universal_agent

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


class HumanFeedbackRequest(BaseModel):
    task_id: str
    reviewer: str = "human_evaluator"
    rating: float = Field(default=1.0, ge=0.0, le=1.0)
    category: str = "correct"  # "correct", "incorrect", "partially_correct", "unsafe", "poor_reasoning"
    comments: Optional[str] = None


class ProposalCreateRequest(BaseModel):
    title: str
    improvement_type: ImprovementType
    target_component: str
    proposed_diff: dict[str, Any]
    rationale: str


@router.get("/tasks")
async def list_evaluated_tasks(limit: int = 50):
    """Lists evaluated task scorecards."""
    records = universal_evaluator.list_evaluations(limit=limit)
    return {"count": len(records), "evaluations": [r.to_dict() for r in records]}


@router.get("/metrics")
async def get_aggregate_metrics():
    """Returns aggregated quality metrics and confidence calibration statistics."""
    report = universal_evaluator.generate_report()
    brier_score = universal_evaluator.calibration_tracker.calculate_brier_score()
    ece_score = universal_evaluator.calibration_tracker.calculate_ece()
    return {
        "report": report,
        "calibration": {
            "brier_score": round(brier_score, 4),
            "expected_calibration_error_ece": round(ece_score, 4),
            "samples_tracked": len(universal_evaluator.calibration_tracker.records),
        },
    }


@router.get("/failures")
async def get_failure_distribution():
    """Returns failure taxonomy distribution and root cause summaries."""
    evals = universal_evaluator.list_evaluations(limit=200)
    failed = [e for e in evals if not e.passed_gate or e.failure_category]
    category_counts: dict[str, int] = {}
    for f in failed:
        cat = f.failure_category or "UNKNOWN"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "total_failures_recorded": len(failed),
        "taxonomy_distribution": category_counts,
        "recent_failures": [
            {
                "task_id": f.task_id,
                "request": f.original_request,
                "category": f.failure_category,
                "root_cause": f.root_cause,
                "suggested_improvements": f.suggested_improvements,
            }
            for f in failed[-20:]
        ],
    }


@router.get("/regressions")
async def list_regressions():
    """Lists persistent regression cases and their run status."""
    cases = universal_evaluator.regression_suite.list_cases()
    return {"count": len(cases), "cases": [c.model_dump() for c in cases]}


@router.get("/benchmarks")
async def get_benchmark_results():
    """Runs and returns golden benchmark results across categories."""
    results = await universal_evaluator.benchmark_framework.run_benchmarks(universal_agent)
    return results


@router.get("/tools")
async def get_tool_reliability_metrics():
    """Returns reliability health metrics across tools."""
    return {"tools": universal_evaluator.tool_monitor.get_all_metrics()}


@router.get("/traces/{task_id}")
async def get_task_trace(task_id: str):
    """Fetches full task execution trajectory with evaluation scorecard."""
    state = universal_agent.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    evaluation = universal_evaluator.get_evaluation(task_id)
    if not evaluation:
        evaluation = universal_evaluator.evaluate(state)

    return {
        "task_id": state.task_id,
        "request": state.original_request,
        "status": state.task_status.value,
        "tool_calls_count": len(state.tool_calls),
        "verifications_count": len(state.verification_results),
        "evaluation": evaluation.to_dict(),
        "state_snapshot": state.model_dump(),
    }


@router.post("/evaluate/{task_id}")
async def evaluate_task_endpoint(task_id: str):
    """Triggers ad-hoc evaluation of a completed or failed task."""
    state = universal_agent.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    res = universal_evaluator.evaluate(state)
    return res.to_dict()


@router.post("/feedback")
async def record_human_feedback(req: HumanFeedbackRequest):
    """Records structured human review feedback for a task."""
    return {"status": "recorded", "feedback": req.model_dump()}


@router.post("/improvement/propose")
async def propose_improvement_endpoint(req: ProposalCreateRequest):
    """Proposes a controlled self-improvement modification."""
    proposal = universal_evaluator.self_improvement_pipeline.propose_improvement(
        title=req.title,
        improvement_type=req.improvement_type,
        target_component=req.target_component,
        proposed_diff=req.proposed_diff,
        rationale=req.rationale,
    )
    return proposal.model_dump()


@router.post("/improvement/validate")
async def validate_improvement_endpoint(proposal_id: str = Query(...)):
    """Runs sandboxed benchmark and regression validation for a proposed improvement."""
    try:
        passed, proposal = await universal_evaluator.self_improvement_pipeline.validate_proposal(
            proposal_id=proposal_id,
            agent_runner=universal_agent,
        )
        return {"passed": passed, "proposal": proposal.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
