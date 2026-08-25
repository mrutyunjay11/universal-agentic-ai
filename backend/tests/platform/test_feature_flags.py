import pytest
from app.platform.feature_flags import FeatureFlagManager


class TestFeatureFlags:
    def test_flag_evaluation_and_tenant_targeting(self):
        ff = FeatureFlagManager()

        # Set tenant targeted flag
        ff.set_flag(
            flag_key="beta_agent_capabilities",
            enabled=True,
            target_tenants=["tenant_vip"],
        )

        assert ff.is_enabled("beta_agent_capabilities", tenant_id="tenant_vip") is True
        assert ff.is_enabled("beta_agent_capabilities", tenant_id="tenant_standard") is False
