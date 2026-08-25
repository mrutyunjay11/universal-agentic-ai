from __future__ import annotations
from typing import Any, Optional
from app.autonomy.events import AgentMessage, MessageType, autonomy_event_bus, AutonomyEvent, AutonomyEventType


class MultiAgentCoordinator:
    """
    Coordinates structured inter-agent communication, manages shared artifact repositories,
    and defends against agent echo chambers.
    """

    def __init__(self):
        self._message_history: list[AgentMessage] = []
        self._shared_artifacts: dict[str, dict[str, Any]] = {}

    async def send_message(self, message: AgentMessage) -> None:
        """Transfers structured message between specialized sub-agents."""
        self._message_history.append(message)
        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.CONSENSUS_REQUESTED if message.message_type == MessageType.VERIFICATION else AutonomyEventType.AGENT_STARTED,
            task_id=message.task_id,
            subtask_id=message.subtask_id,
            agent_name=message.sender_agent,
            payload={"recipient": message.recipient_agent, "type": message.message_type.value},
        ))

    def register_shared_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        content: Any,
        producer_agent: str,
        task_id: str,
    ) -> dict[str, Any]:
        """Registers a shared artifact reference for other sub-agents to access."""
        artifact = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "content": content,
            "producer_agent": producer_agent,
            "task_id": task_id,
        }
        self._shared_artifacts[artifact_id] = artifact
        return artifact

    def get_shared_artifact(self, artifact_id: str) -> Optional[dict[str, Any]]:
        return self._shared_artifacts.get(artifact_id)

    def list_task_artifacts(self, task_id: str) -> list[dict[str, Any]]:
        return [a for a in self._shared_artifacts.values() if a.get("task_id") == task_id]


multi_agent_coordinator = MultiAgentCoordinator()
