from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class AutonomyEventType(str, Enum):
    MASTER_TASK_CREATED = "MASTER_TASK_CREATED"
    TASK_DECOMPOSED = "TASK_DECOMPOSED"
    SUBTASK_CREATED = "SUBTASK_CREATED"
    AGENT_SELECTED = "AGENT_SELECTED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_BLOCKED = "AGENT_BLOCKED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    AGENT_REASSIGNED = "AGENT_REASSIGNED"
    AGENT_CANCELLED = "AGENT_CANCELLED"
    TASK_PARALLELIZED = "TASK_PARALLELIZED"
    TASK_DEPENDENCY_SATISFIED = "TASK_DEPENDENCY_SATISFIED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"
    CONSENSUS_REQUESTED = "CONSENSUS_REQUESTED"
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    WORKFLOW_PAUSED = "WORKFLOW_PAUSED"
    WORKFLOW_RESUMED = "WORKFLOW_RESUMED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"


class MessageType(str, Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    STATUS = "STATUS"
    ARTIFACT = "ARTIFACT"
    QUESTION = "QUESTION"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    VERIFICATION = "VERIFICATION"
    CANCEL = "CANCEL"


class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    sender_agent: str
    recipient_agent: str
    message_type: MessageType
    task_id: str
    subtask_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AutonomyEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"aev_{uuid.uuid4().hex[:8]}")
    event_type: AutonomyEventType
    task_id: str
    subtask_id: Optional[str] = None
    agent_name: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AutonomyEventBus:
    """Pub/Sub event bus for multi-agent autonomy events."""

    def __init__(self):
        self._listeners: list[Any] = []
        self._history: list[AutonomyEvent] = []

    async def emit(self, event: AutonomyEvent) -> None:
        self._history.append(event)
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception:
                pass

    def add_listener(self, listener: Any) -> None:
        self._listeners.append(listener)

    def get_events(self, task_id: Optional[str] = None) -> list[AutonomyEvent]:
        if task_id:
            return [e for e in self._history if e.task_id == task_id]
        return list(self._history)


import asyncio
autonomy_event_bus = AutonomyEventBus()
