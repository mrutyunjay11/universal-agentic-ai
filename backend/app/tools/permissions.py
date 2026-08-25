from __future__ import annotations
from enum import Enum
from typing import Optional


class PermissionTier(str, Enum):
    """
    7-Tier Security Permission Model for Universal Agentic AI Tools.
    Enforces strict capability boundaries for tool execution.
    """
    READ = "read"                      # Safe read-only inspection (auto-approved)
    READ_WRITE = "read_write"          # Workspace mutations with backup snapshot
    EXECUTE = "execute"                # Sandboxed command/process execution
    NETWORK = "network"                # External web/HTTP read access
    EXTERNAL_SYSTEM = "external_system"  # External mutating APIs, databases, cloud systems
    DESTRUCTIVE = "destructive"        # Destructive file/DB operations (requires explicit approval)
    SYSTEM = "system"                  # Privileged system control (process kill, OS config, git commit)


# Permission order from least privileged to most privileged
PERMISSION_LEVELS: dict[PermissionTier, int] = {
    PermissionTier.READ: 0,
    PermissionTier.READ_WRITE: 1,
    PermissionTier.NETWORK: 2,
    PermissionTier.EXECUTE: 3,
    PermissionTier.EXTERNAL_SYSTEM: 4,
    PermissionTier.DESTRUCTIVE: 5,
    PermissionTier.SYSTEM: 6,
}


def check_permission(
    required_tier: PermissionTier,
    granted_tier: PermissionTier,
) -> bool:
    """
    Evaluates whether the granted permission level satisfies the required tool permission.
    """
    req_level = PERMISSION_LEVELS.get(required_tier, 99)
    grant_level = PERMISSION_LEVELS.get(granted_tier, 0)
    return grant_level >= req_level


def requires_human_approval(tier: PermissionTier) -> bool:
    """
    Returns True if the tool execution tier mandates human confirmation by default.
    """
    return tier in (PermissionTier.DESTRUCTIVE, PermissionTier.SYSTEM, PermissionTier.EXTERNAL_SYSTEM)
