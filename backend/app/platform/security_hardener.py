from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class IdentityType(str, Enum):
    HUMAN_USER = "human_user"
    SERVICE_ACCOUNT = "service_account"
    AGENT_IDENTITY = "agent_identity"
    WORKER_IDENTITY = "worker_identity"
    ADMINISTRATOR = "administrator"


class AuthenticatedPrincipal(BaseModel):
    principal_id: str
    identity_type: IdentityType
    tenant_id: str = "default_tenant"
    roles: list[str] = Field(default_factory=lambda: ["user"])
    permissions: list[str] = Field(default_factory=list)


class SecurityHardener:
    """
    Zero-trust security enforcement layer.
    Validates identity attribution, RBAC/ABAC policies, and egress domain allowlists.
    """

    def __init__(self):
        self._domain_allowlist: set[str] = {
            "api.github.com",
            "gitlab.com",
            "googleapis.com",
            "graph.microsoft.com",
            "slack.com",
            "discord.com",
            "amazonaws.com",
        }

    def authorize_action(
        self,
        principal: AuthenticatedPrincipal,
        action: str,
        resource: Optional[str] = None,
    ) -> bool:
        if "admin" in principal.roles or principal.identity_type == IdentityType.ADMINISTRATOR:
            return True

        if action in principal.permissions or "*" in principal.permissions:
            return True

        # Default standard role checks
        if "user" in principal.roles and not action.startswith("system:"):
            return True

        return False

    def validate_egress_domain(self, host: str) -> bool:
        """Enforces network egress restrictions."""
        host_clean = host.lower().strip()
        for allowed in self._domain_allowlist:
            if host_clean == allowed or host_clean.endswith("." + allowed):
                return True
        return False

    def add_allowed_egress_domain(self, domain: str) -> None:
        self._domain_allowlist.add(domain.lower().strip())


security_hardener = SecurityHardener()
