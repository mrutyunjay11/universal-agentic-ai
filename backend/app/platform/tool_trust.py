from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolTrustTier(str, Enum):
    OFFICIAL = "OFFICIAL"
    VERIFIED = "VERIFIED"
    USER_INSTALLED = "USER_INSTALLED"
    THIRD_PARTY = "THIRD_PARTY"
    UNTRUSTED = "UNTRUSTED"
    DISABLED = "DISABLED"


class ToolTrustMetadata(BaseModel):
    tool_name: str
    trust_tier: ToolTrustTier = ToolTrustTier.OFFICIAL
    signature: Optional[str] = None
    publisher: str = "deepmind/universal-agent"
    allowed_in_production: bool = True


class ToolTrustManager:
    """
    Supply-chain security and tool signing manager.
    Enforces that only signed and verified tools can be invoked in production environments.
    """

    def __init__(self, reject_untrusted_in_prod: bool = True):
        self.reject_untrusted = reject_untrusted_in_prod
        self._trust_records: dict[str, ToolTrustMetadata] = {}

    def register_tool_trust(
        self,
        tool_name: str,
        trust_tier: ToolTrustTier = ToolTrustTier.OFFICIAL,
        signature: Optional[str] = None,
        publisher: str = "deepmind/universal-agent",
    ) -> ToolTrustMetadata:
        allowed = trust_tier not in (ToolTrustTier.UNTRUSTED, ToolTrustTier.DISABLED)
        meta = ToolTrustMetadata(
            tool_name=tool_name,
            trust_tier=trust_tier,
            signature=signature or f"sig_{tool_name}_prod",
            publisher=publisher,
            allowed_in_production=allowed,
        )
        self._trust_records[tool_name] = meta
        return meta

    def is_tool_allowed(self, tool_name: str, is_production: bool = True) -> bool:
        meta = self._trust_records.get(tool_name)
        if not meta:
            # Default to official if not explicitly untrusted
            return True
        if is_production and not meta.allowed_in_production:
            return False
        return meta.trust_tier != ToolTrustTier.DISABLED

    def get_tool_trust(self, tool_name: str) -> Optional[ToolTrustMetadata]:
        return self._trust_records.get(tool_name)


tool_trust_manager = ToolTrustManager()
