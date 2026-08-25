from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.integrations.registry import integration_registry
from app.integrations.base import IntegrationContext
from app.integrations.policies import action_approval_manager, ApprovalState
from app.integrations.deployment import deployment_pipeline, DeploymentEnvironment
from app.integrations.events import integration_event_bus

router = APIRouter(tags=["integrations"])


class ConnectRequest(BaseModel):
    credential_reference: Optional[str] = None
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"


class ActionPreviewRequest(BaseModel):
    action_type: str
    provider: str
    target_resource: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "MEDIUM"
    requires_approval: bool = True
    rollback_available: bool = False


@router.get("/api/integrations")
async def list_integrations():
    """Lists all registered external system connectors and their current status."""
    connectors = integration_registry.list_connectors()
    return {
        "count": len(connectors),
        "integrations": [
            {
                "name": c.name,
                "provider": c.provider,
                "capabilities": c.capabilities,
                "auth_methods": c.auth_methods,
            }
            for c in connectors
        ]
    }


@router.get("/api/integrations/{name}")
async def get_integration(name: str):
    """Fetches details for a specific integration connector."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    return {
        "name": conn.name,
        "provider": conn.provider,
        "capabilities": conn.capabilities,
        "auth_methods": conn.auth_methods,
    }


@router.post("/api/integrations/{name}/connect")
async def connect_integration(name: str, req: ConnectRequest):
    """Establishes connection or validates credential reference."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    ctx = IntegrationContext(user_id=req.user_id, tenant_id=req.tenant_id, credential_reference=req.credential_reference)
    success = await conn.connect(ctx)
    return {"name": name, "connected": success}


@router.post("/api/integrations/{name}/disconnect")
async def disconnect_integration(name: str, req: ConnectRequest):
    """Disconnects session and purges active connection state."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    ctx = IntegrationContext(user_id=req.user_id, tenant_id=req.tenant_id)
    success = await conn.disconnect(ctx)
    return {"name": name, "disconnected": success}


@router.get("/api/integrations/{name}/health")
async def get_integration_health(name: str):
    """Fetches health, uptime, and rate limit status for connector."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    return await conn.health_check()


@router.get("/api/integrations/{name}/capabilities")
async def get_integration_capabilities(name: str):
    """Returns list of supported capabilities for connector."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    return {"name": conn.name, "capabilities": conn.get_capabilities()}


@router.get("/api/integrations/{name}/permissions")
async def get_integration_permissions(name: str):
    """Returns permission scopes required by connector."""
    conn = integration_registry.get(name)
    if not conn:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    return {"name": conn.name, "scopes": [f"{name}.read", f"{name}.write"]}


@router.post("/api/external-actions/preview")
async def create_action_preview(req: ActionPreviewRequest):
    """Generates structured pre-execution preview for high-risk external action."""
    preview = action_approval_manager.create_preview(
        action_type=req.action_type,
        provider=req.provider,
        target_resource=req.target_resource,
        parameters=req.parameters,
        risk_level=req.risk_level,
        requires_approval=req.requires_approval,
        rollback_available=req.rollback_available,
    )
    return preview.model_dump()


@router.post("/api/external-actions/{action_id}/approve")
async def approve_external_action(action_id: str):
    """Explicitly approves a pending external action."""
    success = action_approval_manager.approve_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return {"action_id": action_id, "status": "APPROVED"}


@router.post("/api/external-actions/{action_id}/deny")
async def deny_external_action(action_id: str):
    """Denies a pending external action."""
    success = action_approval_manager.deny_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return {"action_id": action_id, "status": "DENIED"}


@router.get("/api/external-actions/{action_id}")
async def get_external_action(action_id: str):
    """Fetches details and approval state of an external action."""
    act = action_approval_manager.get_action(action_id)
    if not act:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return act.model_dump()


@router.get("/api/deployments")
async def list_deployments():
    """Lists all tracked service deployments across environments."""
    deps = deployment_pipeline.list_deployments()
    return {"count": len(deps), "deployments": [d.model_dump() for d in deps]}


@router.get("/api/deployments/{deployment_id}")
async def get_deployment(deployment_id: str):
    """Fetches details and verification status for a deployment."""
    dep = deployment_pipeline.get_deployment(deployment_id)
    if not dep:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")
    return dep.model_dump()


@router.post("/api/deployments/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: str):
    """Triggers rollback to previous verified version."""
    success, msg = deployment_pipeline.rollback(deployment_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"deployment_id": deployment_id, "status": "ROLLED_BACK", "message": msg}


@router.get("/api/integrations/events")
async def get_integration_events():
    """Returns audit log of integration and external system events."""
    events = integration_event_bus.get_events()
    return {"count": len(events), "events": [e.model_dump() for e in events]}
