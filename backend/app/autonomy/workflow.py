from __future__ import annotations
import uuid
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowStage(BaseModel):
    stage_id: str
    name: str
    action_type: str  # "RESEARCH", "CODE", "TEST", "VERIFY", "REPORT"
    condition: Optional[str] = None  # e.g. "test_passed", "evidence_verified"
    next_stages: list[str] = Field(default_factory=list)
    fallback_stage: Optional[str] = None


class PersistentWorkflow(BaseModel):
    workflow_id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:8]}")
    title: str
    stages: dict[str, WorkflowStage] = Field(default_factory=dict)
    current_stage_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.IDLE
    context_data: dict[str, Any] = Field(default_factory=dict)


class PersistentWorkflowEngine:
    """
    Executes and persists stateful multi-stage workflows with dynamic conditional branching.
    """

    def __init__(self):
        self._workflows: dict[str, PersistentWorkflow] = {}

    def create_standard_sdlc_workflow(self, title: str) -> PersistentWorkflow:
        wf = PersistentWorkflow(title=title)
        wf.stages = {
            "research": WorkflowStage(stage_id="research", name="Research", action_type="RESEARCH", next_stages=["code"]),
            "code": WorkflowStage(stage_id="code", name="Implementation", action_type="CODE", next_stages=["test"]),
            "test": WorkflowStage(stage_id="test", name="Testing", action_type="TEST", next_stages=["verify"], fallback_stage="debug"),
            "debug": WorkflowStage(stage_id="debug", name="Debugging", action_type="CODE", next_stages=["test"]),
            "verify": WorkflowStage(stage_id="verify", name="Final Verification", action_type="VERIFY", next_stages=["report"]),
            "report": WorkflowStage(stage_id="report", name="Reporting", action_type="REPORT", next_stages=[]),
        }
        wf.current_stage_id = "research"
        self._workflows[wf.workflow_id] = wf
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[PersistentWorkflow]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[PersistentWorkflow]:
        return list(self._workflows.values())


workflow_engine = PersistentWorkflowEngine()
