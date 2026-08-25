from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

researcher_profile = AgentProfile(
    name="ResearcherAgent",
    role="Research and Evidence Collection Specialist",
    description="Specialized in web search, documentation inspection, academic sources, and source comparison",
    capabilities=["web.search", "web.fetch", "research.compare", "evidence.collect"],
    preferred_tools=["search_web", "fetch_web_page"],
    max_permission_tier=PermissionTier.NETWORK,
    reliability_rating=0.96,
    tags=["research", "web", "facts"],
)
