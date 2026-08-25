import pytest
from app.platform.degraded_mode import DegradedModeManager


class TestDegradedMode:
    def test_fallback_to_keyword_retrieval_on_vector_store_outage(self):
        dmm = DegradedModeManager()

        assert dmm.get_retrieval_strategy() == "HYBRID"
        assert dmm.is_degraded() is False

        # Simulate vector store outage
        dmm.set_subsystem_availability("vector_search", False)

        assert dmm.get_retrieval_strategy() == "KEYWORD_FALLBACK"
        assert dmm.is_degraded() is True
