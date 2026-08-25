from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.policies import ContextSufficiencyStatus
from app.context.planner import ContextPlan
from app.context.evidence import EvidenceItem, RequirementCoverageReport


class SufficiencyEvaluationResult(BaseModel):
    status: ContextSufficiencyStatus
    coverage_score: float
    is_sufficient: bool
    missing_requirements: list[str] = Field(default_factory=list)
    conflicts_detected: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ContextSufficiencyEvaluator:
    """
    Hybrid Context Sufficiency Evaluator.
    Determines whether retrieved context satisfies all mandatory requirements for the reasoning step.
    Combines deterministic requirement coverage scoring with contradiction checks.
    """

    def evaluate_sufficiency(
        self,
        plan: ContextPlan,
        coverage_report: RequirementCoverageReport,
        contradictions: Optional[list[str]] = None,
    ) -> SufficiencyEvaluationResult:
        conflicts = contradictions or []

        if conflicts:
            return SufficiencyEvaluationResult(
                status=ContextSufficiencyStatus.CONFLICTED,
                coverage_score=coverage_report.coverage_score,
                is_sufficient=False,
                missing_requirements=coverage_report.missing_descriptions,
                conflicts_detected=conflicts,
                confidence=0.5,
            )

        if coverage_report.status == "COMPLETE" and coverage_report.missing_count == 0:
            return SufficiencyEvaluationResult(
                status=ContextSufficiencyStatus.SUFFICIENT,
                coverage_score=coverage_report.coverage_score,
                is_sufficient=True,
                missing_requirements=[],
                confidence=0.95,
            )

        if coverage_report.coverage_score >= 0.5:
            return SufficiencyEvaluationResult(
                status=ContextSufficiencyStatus.UNCERTAIN,
                coverage_score=coverage_report.coverage_score,
                is_sufficient=False,
                missing_requirements=coverage_report.missing_descriptions,
                confidence=0.6,
            )

        return SufficiencyEvaluationResult(
            status=ContextSufficiencyStatus.INSUFFICIENT,
            coverage_score=coverage_report.coverage_score,
            is_sufficient=False,
            missing_requirements=coverage_report.missing_descriptions,
            confidence=0.3,
        )


sufficiency_evaluator = ContextSufficiencyEvaluator()
