from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

coder_profile = AgentProfile(
    name="CoderAgent",
    role="Software Engineering and Implementation Specialist",
    description="Specialized in repository exploration, code writing, syntax verification, and test execution",
    capabilities=["file.read", "file.write", "code.analyze", "code.edit", "code.verify"],
    preferred_tools=["write_file", "edit_file", "read_file", "analyze_code", "verify_code"],
    max_permission_tier=PermissionTier.READ_WRITE,
    reliability_rating=0.94,
    tags=["coding", "software", "implementation"],
)
