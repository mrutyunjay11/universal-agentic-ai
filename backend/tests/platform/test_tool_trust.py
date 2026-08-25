import pytest
from app.platform.tool_trust import ToolTrustManager, ToolTrustTier


class TestToolTrust:
    def test_tool_trust_and_untrusted_rejection(self):
        ttm = ToolTrustManager(reject_untrusted_in_prod=True)

        # Register official signed tool
        ttm.register_tool_trust("calculator", ToolTrustTier.OFFICIAL)
        assert ttm.is_tool_allowed("calculator", is_production=True) is True

        # Register untrusted third-party tool
        ttm.register_tool_trust("shady_plugin", ToolTrustTier.UNTRUSTED)
        assert ttm.is_tool_allowed("shady_plugin", is_production=True) is False
