import pytest
from app.evaluation.metrics import (
    QualityDimension,
    CriterionStatus,
    CriterionEvaluation,
    TaskEvaluationResult,
    ConfidenceCalibrationTracker,
)
from app.evaluation.rubric import EvaluationRubric, EvaluationThresholds, EvaluationWeights


class TestEvaluationMetricsAndRubrics:
    def test_task_evaluation_result_scorecard(self):
        res = TaskEvaluationResult(
            task_id="task_test_1",
            original_request="Calculate math expression",
            correctness=0.95,
            completeness=0.90,
            safety=1.0,
            evidence_quality=0.85,
            verification_quality=0.90,
            overall_score=0.92,
            passed_gate=True,
            criteria_results=[
                CriterionEvaluation(criterion="Return numeric result", status=CriterionStatus.PASS, score=1.0)
            ],
        )
        assert res.task_id == "task_test_1"
        assert res.passed_gate is True
        assert res.safety == 1.0
        assert len(res.criteria_results) == 1

    def test_rubric_composite_score_calculation(self):
        rubric = EvaluationRubric()
        score = rubric.compute_composite_score(
            correctness=0.90,
            completeness=0.80,
            relevance=1.0,
            evidence_quality=0.85,
            verification_quality=0.90,
            safety=1.0,
            efficiency=0.70,
            reproducibility=0.95,
        )
        assert 0.85 <= score <= 0.95

    def test_rubric_safety_gate_rejection(self):
        rubric = EvaluationRubric()
        # Safety violation must immediately fail gate
        passed = rubric.evaluate_gate(
            composite_score=0.90,
            correctness=0.90,
            safety=0.0,
            evidence_quality=0.90,
            verification_quality=0.90,
        )
        assert passed is False

    def test_confidence_calibration_tracker(self):
        tracker = ConfidenceCalibrationTracker(num_bins=5)
        # Well-calibrated samples
        tracker.record_outcome(predicted_confidence=0.9, is_correct=True)
        tracker.record_outcome(predicted_confidence=0.8, is_correct=True)
        tracker.record_outcome(predicted_confidence=0.2, is_correct=False)
        tracker.record_outcome(predicted_confidence=0.1, is_correct=False)

        brier = tracker.calculate_brier_score()
        ece = tracker.calculate_ece()

        assert brier < 0.10
        assert ece < 0.25
