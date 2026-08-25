from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.tools.registry import tool_registry
from app.tools.base import ToolCategory, ToolContext
from app.tools.permissions import PermissionTier
from app.tools.audit import audit_logger

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolExecuteRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    project_root: str = "./projects"
    session_id: Optional[str] = None
    permission_granted: PermissionTier = PermissionTier.SYSTEM


@router.get("")
async def list_tools(category: Optional[str] = Query(None, description="Filter by category")):
    cat_enum = None
    if category:
        try:
            cat_enum = ToolCategory(category.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category '{category}'. Available: {[c.value for c in ToolCategory]}")

    tools = tool_registry.list_tools(cat_enum)
    return {
        "total": len(tools),
        "tools": [t.to_schema(format="standard") for t in tools],
    }


@router.get("/categories")
async def list_categories():
    health = tool_registry.health_check()
    return {
        "categories": health["categories"],
        "all_categories": [c.value for c in ToolCategory],
    }


@router.get("/health")
async def get_tools_health():
    return tool_registry.health_check()


@router.get("/audit")
async def get_audit_log(limit: int = Query(50, ge=1, le=200), tool_name: Optional[str] = None):
    events = audit_logger.get_events(limit=limit, tool_name=tool_name)
    return {
        "total_events": len(events),
        "events": [e.model_dump() for e in events],
    }


@router.get("/{name}")
async def get_tool(name: str):
    tool = tool_registry.get(name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
    
    is_avail, reason = tool.check_availability()
    return {
        "schema": tool.to_schema(format="standard"),
        "openai_schema": tool.to_schema(format="openai"),
        "anthropic_schema": tool.to_schema(format="anthropic"),
        "available": is_avail,
        "unavailable_reason": reason,
    }


@router.post("/execute")
async def execute_tool(req: ToolExecuteRequest):
    ctx = ToolContext(
        project_root=req.project_root,
        session_id=req.session_id,
        permission_granted=req.permission_granted,
    )
    result = await tool_registry.execute(req.tool, req.args, ctx)
    return result.model_dump()
