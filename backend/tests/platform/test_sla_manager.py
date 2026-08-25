import pytest
from app.platform.sla_manager import SLAManager


class TestSLAManager:
    def test_availability_and_correctness_slo_compliance(self):
        sm = SLAManager()

        # Both targets met
        res_compliant = sm.compute_slo_status(
            availability_pct=99.95,
            verification_accuracy_pct=99.5,
            p95_latency_ms=1200,
        )
        assert res_compliant["overall_compliant"] is True

        # Correctness breached despite high uptime
        res_breached = sm.compute_slo_status(
            availability_pct=99.99,
            verification_accuracy_pct=92.0,
            p95_latency_ms=1200,
        )
        assert res_breached["overall_compliant"] is False
