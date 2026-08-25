import pytest
from app.autonomy.coordinator import MultiAgentCoordinator
from app.autonomy.events import AgentMessage, MessageType


class TestCoordination:
    @pytest.mark.asyncio
    async def test_inter_agent_messaging_and_artifacts(self):
        coord = MultiAgentCoordinator()

        msg = AgentMessage(
            sender_agent="ResearcherAgent",
            recipient_agent="VerifierAgent",
            message_type=MessageType.VERIFICATION,
            task_id="task_coord_1",
            payload={"claim": "Python 3.12 has subinterpreter support", "sources": ["PEP 684"]},
        )
        await coord.send_message(msg)

        artifact = coord.register_shared_artifact(
            artifact_id="art_data_1",
            artifact_type="dataset",
            content={"rows": 1500},
            producer_agent="DataAnalystAgent",
            task_id="task_coord_1",
        )

        assert artifact["artifact_id"] == "art_data_1"
        fetched = coord.get_shared_artifact("art_data_1")
        assert fetched is not None
        assert fetched["producer_agent"] == "DataAnalystAgent"

        task_artifacts = coord.list_task_artifacts("task_coord_1")
        assert len(task_artifacts) == 1
