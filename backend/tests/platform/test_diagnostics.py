import pytest
from app.platform.diagnostics import SystemDiagnostics


class TestDiagnostics:
    def test_liveness_readiness_and_deep_dependencies(self):
        diag = SystemDiagnostics()

        live = diag.check_liveness()
        assert live["status"] == "LIVE"

        ready = diag.check_readiness()
        assert ready["status"] == "READY"

        deps = diag.check_dependencies()
        assert deps["overall_status"] == "HEALTHY"
        assert len(deps["dependencies"]) >= 6
