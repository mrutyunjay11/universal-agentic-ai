import pytest
from app.autonomy.coordinator import MultiAgentCoordinator


class TestAgentMemoryIsolation:
    def test_shared_vs_private_artifacts(self):
        coord = MultiAgentCoordinator()

        # Shared artifact explicitly registered
        coord.register_shared_artifact(
            artifact_id="pub_art_1",
            artifact_type="report",
            content={"status": "approved"},
            producer_agent="CoderAgent",
            task_id="t_iso_1",
        )

        assert coord.get_shared_artifact("pub_art_1") is not None
        # Unregistered / private artifact should not exist in shared pool
        assert coord.get_shared_artifact("private_reasoning_scratchpad") is None
