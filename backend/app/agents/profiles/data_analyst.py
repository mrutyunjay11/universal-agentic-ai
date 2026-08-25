from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

data_analyst_profile = AgentProfile(
    name="DataAnalystAgent",
    role="Data Processing and Statistical Analysis Specialist",
    description="Specialized in tabular datasets, CSV/JSON processing, descriptive statistics, and numerical validation",
    capabilities=["data.inspect", "data.statistics", "math.calculate", "file.read"],
    preferred_tools=["calculate_statistics", "calculator", "read_file", "verify_calculation"],
    max_permission_tier=PermissionTier.READ,
    reliability_rating=0.96,
    tags=["data", "statistics", "math"],
)
