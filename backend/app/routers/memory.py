from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.memory.manager import memory_manager
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryCreateRequest(BaseModel):
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    scope: MemoryScope = MemoryScope.GLOBAL
    summary: Optional[str] = None
    source: Optional[str] = None
    source_ids: Optional[list[str]] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    confidence: float = 0.8
    importance: float = 0.5
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    importance: Optional[float] = None
    verification_status: Optional[VerificationStatus] = None
    freshness_status: Optional[FreshnessStatus] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    memory_types: Optional[list[MemoryType]] = None
    min_score: float = 0.35
    include_stale: bool = False


class InvalidateRequest(BaseModel):
    reason: str
    new_status: FreshnessStatus = FreshnessStatus.CONTRADICTED
    actor: str = "api_user"


@router.post("/search")
async def search_memory(req: MemorySearchRequest):
    """Hybrid search across memories with scope and relevance filtering."""
    results = await memory_manager.retrieve(
        query=req.query,
        limit=req.limit,
        project_id=req.project_id,
        user_id=req.user_id,
        task_id=req.task_id,
        memory_types=req.memory_types,
        min_score=req.min_score,
        include_stale=req.include_stale,
    )
    return {
        "count": len(results),
        "results": [{"score": round(score, 4), "memory": rec.to_dict()} for score, rec in results],
    }


@router.get("/user")
async def get_user_memories(user_id: str = Query(..., description="User identifier"), limit: int = 50):
    """Retrieves all memories scoped to a specific user."""
    records = await memory_manager.store.list_all(limit=limit, user_id=user_id)
    return {"user_id": user_id, "count": len(records), "memories": [r.to_dict() for r in records]}


@router.get("/project")
async def get_project_memories(project_id: str = Query(..., description="Project identifier"), limit: int = 50):
    """Retrieves all memories scoped to a specific project workspace."""
    records = await memory_manager.store.list_all(limit=limit, project_id=project_id)
    return {"project_id": project_id, "count": len(records), "memories": [r.to_dict() for r in records]}


@router.get("/task")
async def get_task_memories(task_id: str = Query(..., description="Task identifier"), limit: int = 50):
    """Retrieves memories associated with a specific task."""
    records = await memory_manager.store.search(query="", limit=limit, task_id=task_id, include_stale=True)
    return {"task_id": task_id, "count": len(records), "memories": [r.to_dict() for r in records]}


@router.post("", status_code=201)
async def create_memory(req: MemoryCreateRequest):
    """Creates and persists a new memory record."""
    rec = await memory_manager.remember(
        content=req.content,
        memory_type=req.memory_type,
        scope=req.scope,
        summary=req.summary,
        source=req.source,
        source_ids=req.source_ids,
        project_id=req.project_id,
        user_id=req.user_id,
        task_id=req.task_id,
        confidence=req.confidence,
        importance=req.importance,
        verification_status=req.verification_status,
        tags=req.tags,
        metadata=req.metadata,
    )
    return rec.to_dict()


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    """Fetches a specific memory record by ID."""
    rec = await memory_manager.get(memory_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")
    return rec.to_dict()


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, req: MemoryUpdateRequest):
    """Updates an existing memory record."""
    rec = await memory_manager.get(memory_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")

    if req.content is not None:
        rec.content = req.content
    if req.summary is not None:
        rec.summary = req.summary
    if req.confidence is not None:
        rec.confidence = req.confidence
    if req.importance is not None:
        rec.importance = req.importance
    if req.verification_status is not None:
        rec.verification_status = req.verification_status
    if req.freshness_status is not None:
        rec.freshness_status = req.freshness_status
    if req.tags is not None:
        rec.tags = req.tags
    if req.metadata is not None:
        rec.metadata.update(req.metadata)

    rec.version += 1
    updated = await memory_manager.update(rec)
    return updated.to_dict()


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Deletes a memory record."""
    deleted = await memory_manager.forget(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")
    return {"status": "deleted", "memory_id": memory_id}


@router.post("/forget")
async def forget_memory(memory_id: str = Query(...)):
    """Explicitly forgets a memory record."""
    deleted = await memory_manager.forget(memory_id)
    return {"status": "success" if deleted else "not_found", "memory_id": memory_id}


@router.post("/{memory_id}/invalidate")
async def invalidate_memory(memory_id: str, req: InvalidateRequest):
    """Marks a memory as superseded or invalidated with audit logging."""
    audit = await memory_manager.invalidate(memory_id, reason=req.reason, new_status=req.new_status, actor=req.actor)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")
    return {"status": "invalidated", "audit": audit.model_dump()}
