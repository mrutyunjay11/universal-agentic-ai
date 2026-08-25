from __future__ import annotations
import asyncio
import datetime
from enum import Enum
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_UNDERSTOOD = "TASK_UNDERSTOOD"
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_VALIDATED = "PLAN_VALIDATED"
    TOOL_SELECTED = "TOOL_SELECTED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"
    OBSERVATION_CREATED = "OBSERVATION_CREATED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    REFLECTION_COMPLETED = "REFLECTION_COMPLETED"
    REPLAN_CREATED = "REPLAN_CREATED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCELLED = "TASK_CANCELLED"
    STATE_CHANGED = "STATE_CHANGED"


class AgentEvent(BaseModel):
    task_id: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class EventBus:
    def __init__(self):
        self._listeners: list[Callable[[AgentEvent], None]] = []
        self._async_listeners: list[Callable[[AgentEvent], Any]] = []
        self._history: dict[str, list[AgentEvent]] = {}
        self._queues: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, callback: Callable[[AgentEvent], None]):
        self._listeners.append(callback)

    def subscribe_async(self, callback: Callable[[AgentEvent], Any]):
        self._async_listeners.append(callback)

    def get_task_queue(self, task_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if task_id not in self._queues:
            self._queues[task_id] = []
        self._queues[task_id].append(q)
        return q

    def remove_task_queue(self, task_id: str, queue: asyncio.Queue):
        if task_id in self._queues and queue in self._queues[task_id]:
            self._queues[task_id].remove(queue)

    async def emit(self, event: AgentEvent):
        # Store in history
        if event.task_id not in self._history:
            self._history[event.task_id] = []
        self._history[event.task_id].append(event)

        # Notify sync listeners
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

        # Notify async listeners
        for alistener in self._async_listeners:
            try:
                await alistener(event)
            except Exception:
                pass

        # Push to active task queues
        if event.task_id in self._queues:
            for q in self._queues[event.task_id]:
                await q.put(event)

    def get_history(self, task_id: str) -> list[AgentEvent]:
        return self._history.get(task_id, [])


# Global agent event bus
agent_event_bus = EventBus()
