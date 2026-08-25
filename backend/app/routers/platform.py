from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.platform.diagnostics import system_diagnostics
from app.platform.task_queue import task_queue, TaskPriority
from app.platform.worker_pool import worker_pool, WorkerPoolType
from app.platform.cost_governance import cost_governance
from app.platform.tracing import tracer
from app.platform.telemetry import telemetry
from app.platform.alerts import alert_manager
from app.platform.disaster_recovery import disaster_recovery
from app.platform.feature_flags import feature_flags
from app.platform.retention import data_retention

router = APIRouter(tags=["platform"])


class EnqueueTaskRequest(BaseModel):
    task_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = TaskPriority.NORMAL
    pool_type: str = "GENERAL_WORKERS"
    delay_seconds: float = 0.0


class SetBudgetRequest(BaseModel):
    entity_id: str
    max_budget_usd: float


class FeatureFlagRequest(BaseModel):
    flag_key: str
    enabled: bool
    description: str = ""
    rollout_percentage: int = 100


class ForgetPrivacyRequest(BaseModel):
    user_id: str
    tenant_id: str = "default_tenant"


# Health Endpoints (Standard K8s / Cloud Probes)
@router.get("/health")
async def health_root():
    return {"status": "ok", "app": "universal-agent-platform"}


@router.get("/health/live")
async def health_live():
    return system_diagnostics.check_liveness()


@router.get("/health/ready")
async def health_ready():
    return system_diagnostics.check_readiness()


@router.get("/health/dependencies")
async def health_dependencies():
    return system_diagnostics.check_dependencies()


@router.get("/api/platform/diagnostics")
async def get_diagnostics():
    return system_diagnostics.check_dependencies()


@router.get("/api/platform/queue")
async def get_queue_status():
    return {
        "depth": task_queue.get_queue_depth(),
        "dead_letter_count": len(task_queue.get_dead_letter_items()),
    }


@router.post("/api/platform/queue/enqueue")
async def enqueue_task(req: EnqueueTaskRequest):
    item = task_queue.enqueue(
        task_id=req.task_id,
        payload=req.payload,
        priority=req.priority,
        pool_type=req.pool_type,
        delay_seconds=req.delay_seconds,
    )
    return item.model_dump()


@router.get("/api/platform/workers")
async def list_workers():
    workers = worker_pool.list_all_workers()
    return {"count": len(workers), "workers": [w.model_dump() for w in workers]}


@router.get("/api/platform/costs")
async def get_costs():
    return cost_governance.get_summary()


@router.post("/api/platform/budgets")
async def set_budget(req: SetBudgetRequest):
    b = cost_governance.set_budget(req.entity_id, req.max_budget_usd)
    return b.model_dump()


@router.get("/api/platform/traces/{trace_id}")
async def get_trace(trace_id: str):
    spans = tracer.get_trace(trace_id)
    if not spans:
        raise HTTPException(status_code=404, detail=f"Trace '{trace_id}' not found")
    return {"trace_id": trace_id, "spans": [s.model_dump() for s in spans]}


@router.get("/api/platform/metrics")
async def get_platform_metrics():
    return telemetry.get_metrics()


@router.get("/api/platform/alerts")
async def get_platform_alerts():
    alerts = alert_manager.list_all_alerts()
    return {"count": len(alerts), "alerts": [a.model_dump() for a in alerts]}


@router.post("/api/platform/backups/create")
async def create_backup(backup_type: str = "FULL"):
    bk = disaster_recovery.create_backup(backup_type)
    return bk.model_dump()


@router.post("/api/platform/backups/restore-test")
async def restore_test(backup_id: str):
    success, msg = disaster_recovery.test_restoration(backup_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"backup_id": backup_id, "status": "PASSED", "message": msg}


@router.get("/api/platform/feature-flags")
async def get_feature_flags():
    flags = feature_flags.list_flags()
    return {"count": len(flags), "flags": [f.model_dump() for f in flags]}


@router.post("/api/platform/feature-flags")
async def update_feature_flag(req: FeatureFlagRequest):
    f = feature_flags.set_flag(
        flag_key=req.flag_key,
        enabled=req.enabled,
        description=req.description,
        rollout_percentage=req.rollout_percentage,
    )
    return f.model_dump()


@router.post("/api/platform/privacy/forget")
async def forget_user_privacy(req: ForgetPrivacyRequest):
    return data_retention.forget_user_memory(req.user_id, req.tenant_id)
