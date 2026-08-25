import pytest
from app.platform.model_lifecycle import ModelLifecycleManager, ModelProfile


class TestModelFailover:
    def test_model_failover_to_fallback(self):
        mlm = ModelLifecycleManager()

        # Primary is active
        m1 = mlm.resolve_model_or_fallback("gemini-2.5-pro")
        assert m1 is not None
        assert m1.model_id == "gemini-2.5-pro"

        # Simulate primary outage
        mlm._models["gemini-2.5-pro"].status = "DEGRADED"

        # Should failover to fallback
        m_fallback = mlm.resolve_model_or_fallback("gemini-2.5-pro")
        assert m_fallback is not None
        assert m_fallback.model_id == "gemini-2.5-flash"
