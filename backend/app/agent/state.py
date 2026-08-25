from __future__ import annotations
import uuid
import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.tools.permissions import PermissionTier


class TaskState(str, Enum):
    PENDING = "PENDING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    PLAN_VALIDATION = "PLAN_VALIDATION"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    REFLECTING = "REFLECTING"
    REPLANNING = "REPLANNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Valid state transitions
VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PENDING: {TaskState.UNDERSTANDING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.UNDERSTANDING: {TaskState.PLANNING, TaskState.FAILED, TaskState.CANCELLED, TaskState.WAITING_FOR_APPROVAL},
    TaskState.PLANNING: {TaskState.PLAN_VALIDATION, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.PLAN_VALIDATION: {TaskState.EXECUTING, TaskState.PLANNING, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.EXECUTING: {TaskState.OBSERVING, TaskState.WAITING_FOR_APPROVAL, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.OBSERVING: {TaskState.VERIFYING, TaskState.REFLECTING, TaskState.EXECUTING, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.VERIFYING: {TaskState.REFLECTING, TaskState.EXECUTING, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.REFLECTING: {TaskState.EXECUTING, TaskState.REPLANNING, TaskState.COMPLETED, TaskState.FAILED, TaskState.WAITING_FOR_APPROVAL, TaskState.CANCELLED},
    TaskState.REPLANNING: {TaskState.PLAN_VALIDATION, TaskState.PLANNING, TaskState.EXECUTING, TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.WAITING_FOR_APPROVAL: {TaskState.EXECUTING, TaskState.PLANNING, TaskState.REPLANNING, TaskState.CANCELLED, TaskState.FAILED},
    TaskState.COMPLETED: {TaskState.PENDING},  # Reopen / resume operation
    TaskState.FAILED: {TaskState.PENDING},
    TaskState.CANCELLED: {TaskState.PENDING},
}


class TaskType(str, Enum):
    GENERAL_QUESTION = "GENERAL_QUESTION"
    RESEARCH = "RESEARCH"
    FACT_CHECK = "FACT_CHECK"
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    MATHEMATICAL = "MATHEMATICAL"
    SCIENTIFIC = "SCIENTIFIC"
    BROWSER_TASK = "BROWSER_TASK"
    AUTOMATION = "AUTOMATION"
    SYSTEM_TASK = "SYSTEM_TASK"
    MULTI_DOMAIN = "MULTI_DOMAIN"
    UNKNOWN = "UNKNOWN"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class VerificationRequirement(str, Enum):
    NONE = "NONE"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"


class FailureStrategy(str, Enum):
    RETRY = "RETRY"
    RETRY_WITH_MODIFIED_INPUT = "RETRY_WITH_MODIFIED_INPUT"
    ALTERNATIVE_TOOL = "ALTERNATIVE_TOOL"
    ALTERNATIVE_SOURCE = "ALTERNATIVE_SOURCE"
    ROLLBACK = "ROLLBACK"
    REPLAN = "REPLAN"
    ASK_USER = "ASK_USER"
    ABORT = "ABORT"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PlanStep(BaseModel):
    id: str
    description: str
    objective: str
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    tool_name: Optional[str] = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    expected_output: str = ""
    verification_required: VerificationRequirement = VerificationRequirement.OPTIONAL
    failure_strategy: FailureStrategy = FailureStrategy.REPLAN
    risk_level: RiskLevel = RiskLevel.LOW
    status: StepStatus = StepStatus.PENDING
    result_summary: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: int = 0


class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    goal: str
    steps: list[PlanStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    version: int = 1


class StructuredObservation(BaseModel):
    id: str = Field(default_factory=lambda: f"obs_{uuid.uuid4().hex[:8]}")
    step_id: str
    tool_name: str
    summary: str
    raw_reference_id: Optional[str] = None
    success: bool
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    reliability: float = 1.0
    duration_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class VerificationVerdict(BaseModel):
    step_id: str
    claim: str
    status: str  # "verified", "refuted", "inconclusive"
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    verified_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class BudgetStatus(BaseModel):
    max_iterations: int = 20
    current_iterations: int = 0
    max_tool_calls: int = 50
    current_tool_calls: int = 0
    max_execution_time_seconds: float = 600.0
    elapsed_time_seconds: float = 0.0
    max_tokens: int = 100000
    used_tokens: int = 0

    @property
    def is_exhausted(self) -> bool:
        return (
            self.current_iterations >= self.max_iterations
            or self.current_tool_calls >= self.max_tool_calls
            or self.elapsed_time_seconds >= self.max_execution_time_seconds
            or self.used_tokens >= self.max_tokens
        )


class AgentState(BaseModel):
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")

    original_request: str
    normalized_goal: str = ""

    task_type: TaskType = TaskType.UNKNOWN
    task_status: TaskState = TaskState.PENDING

    plan: Optional[Plan] = None
    current_step_index: int = 0

    observations: list[StructuredObservation] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)

    evidence: list[dict[str, Any]] = Field(default_factory=list)
    verification_results: list[VerificationVerdict] = Field(default_factory=list)

    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    context: dict[str, Any] = Field(default_factory=dict)
    memory_references: list[str] = Field(default_factory=list)

    user_approvals: list[dict[str, Any]] = Field(default_factory=list)
    pending_approval: Optional[dict[str, Any]] = None

    files_changed: list[str] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)

    iteration_count: int = 0
    budget: BudgetStatus = Field(default_factory=BudgetStatus)

    permission_granted: PermissionTier = PermissionTier.READ_WRITE
    confidence: float = 0.0
    final_result: Optional[dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def transition_to(self, new_state: TaskState) -> bool:
        allowed = VALID_TRANSITIONS.get(self.task_status, set())
        if new_state not in allowed:
            raise ValueError(f"Invalid state transition: {self.task_status.value} -> {new_state.value}")
        self.task_status = new_state
        self.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return True
