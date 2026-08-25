from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

debugger_profile = AgentProfile(
    name="DebuggerAgent",
    role="Root Cause Diagnosis and Bug Remediation Specialist",
    description="Specialized in reproducing errors, analyzing stack traces, isolating regressions, and applying fixes",
    capabilities=["code.debug", "code.analyze", "code.edit", "terminal.run"],
    preferred_tools=["analyze_code", "edit_file", "execute_command", "verify_code"],
    max_permission_tier=PermissionTier.READ_WRITE,
    reliability_rating=0.92,
    tags=["debug", "troubleshooting", "patching"],
)
