from __future__ import annotations
from app.autonomy.agent_profile import AgentProfile
from app.tools.permissions import PermissionTier

verifier_profile = AgentProfile(
    name="VerifierAgent",
    role="Independent Verification and Ground Truth Validator",
    description="Specialized in independent empirical verification, mathematical validation, code testing, and contradiction detection",
    capabilities=["verify.claim", "verify.source", "math.calculate", "code.verify"],
    preferred_tools=["verify_claim", "verify_calculation", "verify_code", "verify_source_authority"],
    max_permission_tier=PermissionTier.READ,
    reliability_rating=0.98,
    tags=["verifier", "ground_truth", "validation"],
)
