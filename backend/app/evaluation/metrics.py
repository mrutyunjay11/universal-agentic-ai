from __future__ import annotations
import math
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class QualityDimension(str, Enum):
    CORRECTNESS = "CORRECTNESS"
    COMPLETENESS = "COMPLETENESS"
    RELEVANCE = "RELEVANCE"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    VERIFICATION_QUALITY = "VERIFICATION_QUALITY"
    SAFETY = "SAFETY"
    EFFICIENCY = "EFFICIENCY"
    REPRODUCIBILITY = "REPRODUCIBILITY"


class CriterionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class CriterionEvaluation(BaseModel):
    criterion: str
    status: CriterionStatus = CriterionStatus.UNKNOWN
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""
    evidence_references: list[str] = Field(default_factory=list)


class TaskEvaluationResult(BaseModel):
    """
    Standardized evaluation scorecard for a completed or failed agent task execution.
    Maintains independent scores across all quality dimensions rather than collapsing them.
    """
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:10]}")
    task_id: str
    original_request: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Multi-dimensional quality scores [0.0 - 1.0]
    correctness: float = Field(default=1.0, ge=0.0, le=1.0)
    completeness: float = Field(default=1.0, ge=0.0, le=1.0)
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    verification_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    safety: float = Field(default=1.0, ge=0.0, le=1.0)
    efficiency: float = Field(default=1.0, ge=0.0, le=1.0)
    reproducibility: float = Field(default=1.0, ge=0.0, le=1.0)

    # Composite overall score
    overall_score: float = Field(default=1.0, ge=0.0, le=1.0)
    passed_gate: bool = True

    # Criterion breakdown
    criteria_results: list[CriterionEvaluation] = Field(default_factory=list)

    # Diagnostic metadata
    safety_violations: list[str] = Field(default_factory=list)
    failure_category: Optional[str] = None
    root_cause: Optional[str] = None
    suggested_improvements: list[str] = Field(default_factory=list)
    execution_duration_ms: int = 0
    total_tool_calls: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class ConfidenceCalibrationTracker:
    """
    Tracks predicted agent confidence against empirical correctness to detect overconfidence
    and calculate Expected Calibration Error (ECE) and Brier scores.
    """

    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins
        # List of (predicted_confidence, actual_is_correct)
        self.records: list[tuple[float, bool]] = []

    def record_outcome(self, predicted_confidence: float, is_correct: bool) -> None:
        conf = max(0.0, min(1.0, float(predicted_confidence)))
        self.records.append((conf, bool(is_correct)))

    def calculate_brier_score(self) -> float:
        """Computes mean squared error of probability predictions."""
        if not self.records:
            return 0.0
        return sum((conf - (1.0 if correct else 0.0)) ** 2 for conf, correct in self.records) / len(self.records)

    def calculate_ece(self) -> float:
        """Computes Expected Calibration Error (ECE)."""
        if not self.records:
            return 0.0

        bin_size = 1.0 / self.num_bins
        total_samples = len(self.records)
        ece = 0.0

        for i in range(self.num_bins):
            bin_min = i * bin_size
            bin_max = (i + 1) * bin_size
            bin_items = [
                (conf, correct)
                for conf, correct in self.records
                if bin_min <= conf < bin_max or (i == self.num_bins - 1 and conf == 1.0)
            ]
            if not bin_items:
                continue

            avg_confidence = sum(conf for conf, _ in bin_items) / len(bin_items)
            avg_accuracy = sum(1.0 for _, correct in bin_items if correct) / len(bin_items)
            bin_weight = len(bin_items) / total_samples

            ece += bin_weight * abs(avg_accuracy - avg_confidence)

        return ece


calibration_tracker = ConfidenceCalibrationTracker()
