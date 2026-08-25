from __future__ import annotations
import uuid
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class IntegrationStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


class IntegrationContext(BaseModel):
    """Execution context provided to integration connectors."""
    user_id: str = "default_user"
    project_id: Optional[str] = None
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    permissions: list[str] = Field(default_factory=list)
    credential_reference: Optional[str] = None
    idempotency_key: Optional[str] = None
    tenant_id: str = "default_tenant"


class IntegrationResult(BaseModel):
    """Standardized result returned by external system connectors."""
    integration_name: str
    action: str
    status: str = "SUCCESS"
    data: Any = None
    duration_ms: int = 0
    idempotency_key: Optional[str] = None
    error: Optional[str] = None
    reconciliation_state: Optional[dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Integration(ABC):
    """
    Abstract base class for all real-world system integrations.
    Guarantees strict schema validation, opaque credential reference resolution,
    health monitoring, and state reconciliation.
    """
    name: str
    provider: str
    capabilities: list[str] = []
    auth_methods: list[str] = ["api_key", "oauth2"]

    @abstractmethod
    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        """Establishes connection or validates credentials."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self, context: IntegrationContext) -> bool:
        """Purges active connection state or session."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Returns health, authentication status, and rate limit info."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        """Executes a specific capability on the external system."""
        raise NotImplementedError

    def get_capabilities(self) -> list[str]:
        return list(self.capabilities)
