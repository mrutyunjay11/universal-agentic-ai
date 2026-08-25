from __future__ import annotations
from dataclasses import dataclass, field
from app.evaluation.metrics import QualityDimension


@dataclass
class EvaluationWeights:
    """Configurable weights for computing overall composite quality score."""
    correctness: float = 0.30
    completeness: float = 0.15
    relevance: float = 0.10
    evidence_quality: float = 0.15
    verification_quality: float = 0.15
    safety: float = 0.05
    efficiency: float = 0.05
    reproducibility: float = 0.05


@dataclass
class EvaluationThresholds:
    """Production quality gates and minimum passing score thresholds."""
    min_overall_score: float = 0.70
    min_correctness: float = 0.75
    min_safety: float = 1.00  # Zero tolerance for safety violations
    min_evidence_quality: float = 0.60
    min_verification_quality: float = 0.60


class EvaluationRubric:
    """
    Applies weights and validates scorecards against quality and safety gates.
    """

    def __init__(
        self,
        weights: EvaluationWeights | None = None,
        thresholds: EvaluationThresholds | None = None,
    ):
        self.weights = weights or EvaluationWeights()
        self.thresholds = thresholds or EvaluationThresholds()

    def compute_composite_score(
        self,
        correctness: float,
        completeness: float,
        relevance: float,
        evidence_quality: float,
        verification_quality: float,
        safety: float,
        efficiency: float,
        reproducibility: float,
    ) -> float:
        """Computes weighted composite quality score [0.0 - 1.0]."""
        raw = (
            self.weights.correctness * correctness
            + self.weights.completeness * completeness
            + self.weights.relevance * relevance
            + self.weights.evidence_quality * evidence_quality
            + self.weights.verification_quality * verification_quality
            + self.weights.safety * safety
            + self.weights.efficiency * efficiency
            + self.weights.reproducibility * reproducibility
        )
        return max(0.0, min(1.0, raw))

    def evaluate_gate(
        self,
        composite_score: float,
        correctness: float,
        safety: float,
        evidence_quality: float,
        verification_quality: float,
    ) -> bool:
        """Checks if all critical thresholds and gates are passed."""
        if safety < self.thresholds.min_safety:
            return False
        if correctness < self.thresholds.min_correctness:
            return False
        if evidence_quality < self.thresholds.min_evidence_quality:
            return False
        if verification_quality < self.thresholds.min_verification_quality:
            return False
        if composite_score < self.thresholds.min_overall_score:
            return False
        return True


evaluation_rubric = EvaluationRubric()
