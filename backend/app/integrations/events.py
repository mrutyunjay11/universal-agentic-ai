from __future__ import annotations
import uuid
import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class IntegrationEventType(str, Enum):
    WEBHOOK_RECEIVED = "WEBHOOK_RECEIVED"
    EXTERNAL_ACTION_PREVIEWED = "EXTERNAL_ACTION_PREVIEWED"
    EXTERNAL_ACTION_APPROVED = "EXTERNAL_ACTION_APPROVED"
    EXTERNAL_ACTION_EXECUTED = "EXTERNAL_ACTION_EXECUTED"
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_COMPLETED = "DEPLOYMENT_COMPLETED"
    DEPLOYMENT_ROLLED_BACK = "DEPLOYMENT_ROLLED_BACK"
    INCIDENT_DETECTED = "INCIDENT_DETECTED"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"


class IntegrationEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"intev_{uuid.uuid4().hex[:8]}")
    event_type: IntegrationEventType
    provider: str
    resource_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class IntegrationEventBus:
    """Pub/Sub event bus for integration and external system events."""

    def __init__(self):
        self._history: list[IntegrationEvent] = []

    def emit(self, event: IntegrationEvent) -> None:
        self._history.append(event)

    def get_events(self, provider: Optional[str] = None) -> list[IntegrationEvent]:
        if provider:
            return [e for e in self._history if e.provider == provider]
        return list(self._history)


integration_event_bus = IntegrationEventBus()
