from __future__ import annotations
import asyncio
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.agent.agent import universal_agent
from app.agent.state import AgentState, TaskState
from app.agent.events import agent_event_bus
from app.tools.permissions import PermissionTier

router = APIRouter(prefix="/api/agent", tags=["agent"])


class CreateTaskRequest(BaseModel):
    request: str = Field(..., description="User's natural language goal or instruction")
    session_id: Optional[str] = None
    permission_granted: PermissionTier = PermissionTier.READ_WRITE
    async_execution: bool = False


class TaskApprovalRequest(BaseModel):
    approved: bool = True
    comment: Optional[str] = None


@router.post("/tasks", response_model=dict[str, Any])
async def create_agent_task(payload: CreateTaskRequest, background_tasks: BackgroundTasks):
    state = universal_agent.create_task(
        request=payload.request,
        session_id=payload.session_id,
        permission_granted=payload.permission_granted,
    )

    if payload.async_execution:
        background_tasks.add_task(universal_agent.run_task, state)
        return {
            "task_id": state.task_id,
            "session_id": state.session_id,
            "status": state.task_status.value,
            "message": "Task queued for background execution.",
        }
    else:
        completed_state = await universal_agent.run_task(state)
        return {
            "task_id": completed_state.task_id,
            "session_id": completed_state.session_id,
            "status": completed_state.task_status.value,
            "goal": completed_state.normalized_goal,
            "final_result": completed_state.final_result,
            "confidence": completed_state.confidence,
            "errors": completed_state.errors,
        }


@router.get("/tasks/{task_id}", response_model=dict[str, Any])
async def get_task_info(task_id: str):
    state = universal_agent.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return {
        "task_id": state.task_id,
        "session_id": state.session_id,
        "status": state.task_status.value,
        "goal": state.normalized_goal,
        "task_type": state.task_type.value,
        "iteration_count": state.iteration_count,
        "tool_calls_count": len(state.tool_calls),
        "evidence_count": len(state.evidence),
        "verifications_count": len(state.verification_results),
        "pending_approval": state.pending_approval,
        "final_result": state.final_result,
    }


@router.get("/tasks/{task_id}/state", response_model=dict[str, Any])
async def get_task_full_state(task_id: str):
    state = universal_agent.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return state.model_dump()


@router.get("/tasks/{task_id}/events", response_model=list[dict[str, Any]])
async def get_task_events(task_id: str):
    events = agent_event_bus.get_history(task_id)
    return [e.model_dump() for e in events]


@router.post("/tasks/{task_id}/resume", response_model=dict[str, Any])
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    state = universal_agent.get_task(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    resumed_state = await universal_agent.resume_task(task_id, approved=True)
    if not resumed_state:
        raise HTTPException(status_code=400, detail="Failed to resume task")

    return {
        "task_id": resumed_state.task_id,
        "status": resumed_state.task_status.value,
        "final_result": resumed_state.final_result,
    }


@router.post("/tasks/{task_id}/cancel", response_model=dict[str, Any])
async def cancel_task(task_id: str):
    cancelled = await universal_agent.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {"task_id": task_id, "status": "CANCELLED"}


@router.post("/tasks/{task_id}/approval", response_model=dict[str, Any])
async def task_approval(task_id: str, payload: TaskApprovalRequest):
    resumed = await universal_agent.resume_task(task_id, approved=payload.approved)
    if not resumed:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found or not in WAITING_FOR_APPROVAL")
    return {
        "task_id": task_id,
        "status": resumed.task_status.value,
        "approved": payload.approved,
    }
