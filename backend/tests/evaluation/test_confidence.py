import pytest
from app.evaluation.metrics import ConfidenceCalibrationTracker


class TestConfidenceCalibration:
    def test_overconfidence_detection(self):
        tracker = ConfidenceCalibrationTracker(num_bins=5)

        # Record severely overconfident agent predictions (confidence 0.99, but all failed)
        for _ in range(5):
            tracker.record_outcome(predicted_confidence=0.99, is_correct=False)

        ece = tracker.calculate_ece()
        brier = tracker.calculate_brier_score()

        # ECE and Brier score must be very high for overconfident predictions
        assert ece > 0.80
        assert brier > 0.80
