from __future__ import annotations
import time
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field
from app.context.planner import ContextPlan
from app.context.evidence import EvidenceItem, evidence_manager, RequirementCoverageReport
from app.context.sufficiency import sufficiency_evaluator, SufficiencyEvaluationResult


class InformationGaps(BaseModel):
    missing: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    next_queries: list[str] = Field(default_factory=list)
    iteration: int = 1


class IterativeRetrievalEngine:
    """
    Iterative Retrieval & Reasoning Engine.
    Executes targeted multi-step retrieval loops with strict progress detection,
    preventing infinite searches and halting upon diminishing returns.
    """

    def __init__(self, max_iterations: int = 3, min_progress_delta: float = 0.05):
        self.max_iterations = max_iterations
        self.min_progress_delta = min_progress_delta

    def identify_information_gaps(
        self,
        plan: ContextPlan,
        coverage: RequirementCoverageReport,
        contradictions: Optional[list[str]] = None,
        current_iteration: int = 1,
    ) -> InformationGaps:
        next_queries = [
            f"{plan.task} {desc}" for desc in coverage.missing_descriptions
        ]
        return InformationGaps(
            missing=coverage.missing_descriptions,
            conflicts=contradictions or [],
            next_queries=next_queries[:3],
            iteration=current_iteration,
        )

    def should_continue_retrieval(
        self,
        current_iteration: int,
        prev_coverage_score: float,
        curr_coverage_score: float,
        sufficiency: SufficiencyEvaluationResult,
    ) -> tuple[bool, str]:
        if sufficiency.is_sufficient:
            return False, "Context is fully sufficient"

        if current_iteration >= self.max_iterations:
            return False, f"Maximum retrieval iterations ({self.max_iterations}) reached"

        if current_iteration > 1:
            delta = curr_coverage_score - prev_coverage_score
            if delta < self.min_progress_delta:
                return False, f"Diminishing returns detected (progress delta {delta:.3f} < {self.min_progress_delta})"

        return True, "Continuing targeted retrieval"


iterative_retrieval_engine = IterativeRetrievalEngine()
