from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.tools.permissions import PermissionTier


class AgentStateEnum(str, Enum):
    CREATED = "CREATED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TERMINATED = "TERMINATED"


class AgentProfile(BaseModel):
    """
    Defines the role, capabilities, preferred tools, model preferences, and risk tolerance
    for a specialized sub-agent.
    """
    id: str = Field(default_factory=lambda: f"profile_{uuid.uuid4().hex[:8]}")
    name: str
    role: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    preferred_tools: list[str] = Field(default_factory=list)
    preferred_model: str = "primary"
    max_permission_tier: PermissionTier = PermissionTier.READ_WRITE
    verification_policy: dict[str, Any] = Field(default_factory=dict)
    risk_tolerance: str = "LOW"
    reliability_rating: float = 0.95
    tags: list[str] = Field(default_factory=list)

    def matches_capabilities(self, required_capabilities: list[str]) -> float:
        """Computes capability match score [0.0 - 1.0]."""
        if not required_capabilities:
            return 0.5
        matched = sum(
            1 for req in required_capabilities
            if any(req.lower() in cap.lower() or cap.lower() in req.lower() for cap in self.capabilities)
        )
        return matched / len(required_capabilities)
