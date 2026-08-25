from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

document_analyst_profile = AgentProfile(
    name="DocumentAnalystAgent",
    role="Document Processing and Report Synthesis Specialist",
    description="Specialized in PDF inspection, markdown structuring, table extraction, and cross-document comparison",
    capabilities=["file.read", "document.extract", "document.compare"],
    preferred_tools=["read_file", "list_directory"],
    max_permission_tier=PermissionTier.READ,
    reliability_rating=0.93,
    tags=["documents", "reports", "pdf"],
)
