from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.autonomy.orchestrator import master_orchestrator
from app.autonomy.policies import ExecutionMode
from app.autonomy.agent_pool import agent_pool
from app.autonomy.long_horizon import long_horizon_manager
from app.autonomy.coordinator import multi_agent_coordinator
from app.autonomy.events import autonomy_event_bus
from app.autonomy.workflow import workflow_engine

router = APIRouter(prefix="/api/autonomy", tags=["autonomy"])


class CreateMasterTaskRequest(BaseModel):
    goal: str
    execution_mode: Optional[ExecutionMode] = None
    context: Optional[dict[str, Any]] = None


@router.post("/tasks")
async def create_and_run_task(req: CreateMasterTaskRequest):
    """Submits and initiates an autonomous single or multi-agent task."""
    record = master_orchestrator.create_task(
        goal=req.goal,
        execution_mode=req.execution_mode,
        context=req.context,
    )
    result = await master_orchestrator.execute_task(record.task_id)
    return result.model_dump()


@router.get("/tasks/{task_id}")
async def get_master_task(task_id: str):
    """Returns details and current status of a master task."""
    record = master_orchestrator.get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return record.model_dump()


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pauses long-horizon execution of a task."""
    long_horizon_manager.pause_task(task_id)
    return {"status": "paused", "task_id": task_id}


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resumes paused task from checkpoint."""
    long_horizon_manager.resume_task(task_id)
    return {"status": "resumed", "task_id": task_id}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Safely cancels all executing subtasks under master task."""
    graph = master_orchestrator.get_task_graph(task_id)
    if graph:
        from app.autonomy.dispatcher import task_dispatcher
        for s_id in graph.nodes:
            task_dispatcher.cancel_subtask(s_id)
    return {"status": "cancelled", "task_id": task_id}


@router.get("/tasks/{task_id}/graph")
async def get_task_graph_endpoint(task_id: str):
    """Returns the SubTask DAG structure for a master task."""
    graph = master_orchestrator.get_task_graph(task_id)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Task graph for '{task_id}' not found")
    return graph.to_dict()


@router.get("/tasks/{task_id}/agents")
async def get_task_agents(task_id: str):
    """Lists sub-agents assigned to subtasks of this master task."""
    graph = master_orchestrator.get_task_graph(task_id)
    if not graph:
        return {"agents": []}
    agents = list(set(s.assigned_agent for s in graph.nodes.values() if s.assigned_agent))
    return {"task_id": task_id, "agents": agents}


@router.get("/tasks/{task_id}/events")
async def get_task_events(task_id: str):
    """Returns audit log of autonomy events for this task."""
    events = autonomy_event_bus.get_events(task_id)
    return {"task_id": task_id, "count": len(events), "events": [e.model_dump() for e in events]}


@router.get("/tasks/{task_id}/artifacts")
async def get_task_artifacts(task_id: str):
    """Returns shared artifacts generated across subtasks."""
    artifacts = multi_agent_coordinator.list_task_artifacts(task_id)
    return {"task_id": task_id, "count": len(artifacts), "artifacts": artifacts}


@router.get("/agents")
async def list_agent_profiles():
    """Lists registered specialized agent profiles."""
    profiles = agent_pool.list_profiles()
    return {"count": len(profiles), "agents": [p.model_dump() for p in profiles]}


@router.get("/agents/{agent_id}")
async def get_agent_profile(agent_id: str):
    """Fetches details for a specific agent profile."""
    profile = agent_pool.get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Agent profile '{agent_id}' not found")
    return profile.model_dump()


@router.get("/workflows")
async def list_workflows():
    """Lists persistent workflows."""
    wfs = workflow_engine.list_workflows()
    return {"count": len(wfs), "workflows": [w.model_dump() for w in wfs]}
