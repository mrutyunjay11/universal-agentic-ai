from __future__ import annotations
from typing import Any


class DegradedModeManager:
    """
    Manages degraded-mode fallbacks when non-critical auxiliary infrastructure suffers outages.
    Preserves core deterministic task execution.
    """

    def __init__(self):
        self.vector_search_available = True
        self.advanced_reasoning_available = True
        self.real_time_monitoring_available = True

    def set_subsystem_availability(self, subsystem: str, available: bool) -> None:
        if subsystem == "vector_search":
            self.vector_search_available = available
        elif subsystem == "advanced_reasoning":
            self.advanced_reasoning_available = available
        elif subsystem == "monitoring":
            self.real_time_monitoring_available = available

    def get_retrieval_strategy(self) -> str:
        """Returns HYBRID, VECTOR_ONLY, or KEYWORD_FALLBACK."""
        if self.vector_search_available:
            return "HYBRID"
        return "KEYWORD_FALLBACK"

    def is_degraded(self) -> bool:
        return not (self.vector_search_available and self.advanced_reasoning_available and self.real_time_monitoring_available)


degraded_mode_manager = DegradedModeManager()
