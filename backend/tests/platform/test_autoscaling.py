import pytest
from app.platform.autoscaler import Autoscaler


class TestAutoscaling:
    def test_scale_up_on_high_queue_depth(self):
        scaler = Autoscaler(min_workers=1, max_workers=10, cooldown_seconds=0.0)

        decision = scaler.evaluate_scaling(
            pool_type="GENERAL_WORKERS",
            current_workers=2,
            queue_depth=15,
            avg_worker_utilization_pct=90.0,
        )

        assert decision.action == "SCALE_UP"
        assert decision.target_workers > 2

    def test_scale_down_on_idle_workload(self):
        scaler = Autoscaler(min_workers=1, max_workers=10, cooldown_seconds=0.0)

        decision = scaler.evaluate_scaling(
            pool_type="GENERAL_WORKERS",
            current_workers=5,
            queue_depth=0,
            avg_worker_utilization_pct=10.0,
        )

        assert decision.action == "SCALE_DOWN"
        assert decision.target_workers == 4
