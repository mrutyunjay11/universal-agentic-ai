from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

generalist_profile = AgentProfile(
    name="GeneralistAgent",
    role="General-Purpose Autonomous Worker",
    description="Fallback generalist worker for multi-capability tasks and standard execution",
    capabilities=["file.read", "file.write", "web.search", "math.calculate"],
    preferred_tools=["search_web", "calculator", "read_file", "write_file"],
    max_permission_tier=PermissionTier.READ_WRITE,
    reliability_rating=0.90,
    tags=["generalist", "default"],
)
