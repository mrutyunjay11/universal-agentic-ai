from __future__ import annotations
import asyncio
from typing import Any, Optional
from app.autonomy.task_graph import SubTask
from app.autonomy.delegation import delegation_engine
from app.autonomy.events import autonomy_event_bus, AutonomyEvent, AutonomyEventType
from app.agents.base import AgentResult


class TaskDispatcher:
    """
    Dispatches scheduled subtasks to assigned specialized agents, monitors execution,
    and manages task cancellation tokens.
    """

    def __init__(self):
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._cancelled_tasks: set[str] = set()

    async def dispatch(
        self,
        subtask: SubTask,
        parent_context: Optional[dict[str, Any]] = None,
    ) -> AgentResult:
        if subtask.id in self._cancelled_tasks:
            return AgentResult(
                subtask_id=subtask.id,
                agent_name="Dispatcher",
                status=subtask.status,
                summary=f"Subtask '{subtask.id}' was cancelled before execution",
            )

        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.AGENT_STARTED,
            task_id=subtask.parent_task_id,
            subtask_id=subtask.id,
            agent_name=subtask.assigned_agent,
            payload={"objective": subtask.objective},
        ))

        coro = delegation_engine.delegate_subtask(subtask, parent_context)
        task_future = asyncio.create_task(coro)
        self._active_tasks[subtask.id] = task_future

        try:
            result: AgentResult = await task_future
            event_type = (
                AutonomyEventType.AGENT_COMPLETED
                if result.status.value == "COMPLETED"
                else AutonomyEventType.AGENT_FAILED
            )
            await autonomy_event_bus.emit(AutonomyEvent(
                event_type=event_type,
                task_id=subtask.parent_task_id,
                subtask_id=subtask.id,
                agent_name=result.agent_name,
                payload={"summary": result.summary, "errors": result.errors},
            ))
            return result
        finally:
            self._active_tasks.pop(subtask.id, None)

    def cancel_subtask(self, subtask_id: str) -> bool:
        self._cancelled_tasks.add(subtask_id)
        if subtask_id in self._active_tasks:
            self._active_tasks[subtask_id].cancel()
            return True
        return False


task_dispatcher = TaskDispatcher()
