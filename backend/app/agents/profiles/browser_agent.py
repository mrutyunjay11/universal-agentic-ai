from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

browser_agent_profile = AgentProfile(
    name="BrowserAgent",
    role="Web Browsing and Interactive DOM Extraction Specialist",
    description="Specialized in fetching complex dynamic web pages, interactive navigation, and web data extraction",
    capabilities=["web.browser", "web.fetch", "web.search"],
    preferred_tools=["fetch_web_page", "search_web"],
    max_permission_tier=PermissionTier.NETWORK,
    reliability_rating=0.91,
    tags=["browser", "web", "dom"],
)
