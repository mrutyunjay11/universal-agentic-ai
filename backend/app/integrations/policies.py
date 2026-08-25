from __future__ import annotations
import uuid
import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class IntegrationScope(str, Enum):
    # Git
    GITHUB_READ = "github.read"
    GITHUB_WRITE = "github.write"
    GITLAB_READ = "gitlab.read"
    GITLAB_WRITE = "gitlab.write"

    # Communication & Email
    EMAIL_READ = "email.read"
    EMAIL_SEND = "email.send"
    CALENDAR_READ = "calendar.read"
    CALENDAR_WRITE = "calendar.write"
    SLACK_READ = "slack.read"
    SLACK_SEND = "slack.send"
    DISCORD_SEND = "discord.send"

    # Storage & Cloud
    STORAGE_READ = "storage.read"
    STORAGE_WRITE = "storage.write"
    CLOUD_READ = "cloud.read"
    CLOUD_WRITE = "cloud.write"

    # Containers & Deployment
    DOCKER_RUN = "docker.run"
    K8S_READ = "k8s.read"
    K8S_APPLY = "k8s.apply"
    DEPLOYMENT_STAGING = "deployment.staging"
    DEPLOYMENT_PROD = "deployment.prod"

    # Database
    DATABASE_READ = "database.read"
    DATABASE_WRITE = "database.write"


class ApprovalState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ExternalActionPreview(BaseModel):
    id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    action_type: str
    provider: str
    target_resource: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    requires_approval: bool = True
    approval_state: ApprovalState = ApprovalState.PENDING
    rollback_available: bool = False
    compensation_plan: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    executed_at: Optional[str] = None


class ExternalActionApprovalManager:
    """Manages pre-execution previews, high-risk mutation approval gates, and state transitions."""

    def __init__(self):
        self._actions: dict[str, ExternalActionPreview] = {}

    def create_preview(
        self,
        action_type: str,
        provider: str,
        target_resource: str,
        parameters: dict[str, Any],
        risk_level: str = "MEDIUM",
        requires_approval: bool = True,
        rollback_available: bool = False,
    ) -> ExternalActionPreview:
        preview = ExternalActionPreview(
            action_type=action_type,
            provider=provider,
            target_resource=target_resource,
            parameters=parameters,
            risk_level=risk_level,
            requires_approval=requires_approval,
            approval_state=ApprovalState.PENDING if requires_approval else ApprovalState.APPROVED,
            rollback_available=rollback_available,
        )
        self._actions[preview.id] = preview
        return preview

    def approve_action(self, action_id: str) -> bool:
        if action_id in self._actions:
            self._actions[action_id].approval_state = ApprovalState.APPROVED
            return True
        return False

    def deny_action(self, action_id: str) -> bool:
        if action_id in self._actions:
            self._actions[action_id].approval_state = ApprovalState.DENIED
            return True
        return False

    def get_action(self, action_id: str) -> Optional[ExternalActionPreview]:
        return self._actions.get(action_id)


action_approval_manager = ExternalActionApprovalManager()
