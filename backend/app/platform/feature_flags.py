from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class FeatureFlag(BaseModel):
    flag_key: str
    enabled: bool = False
    description: str = ""
    rollout_percentage: int = 100
    target_tenants: list[str] = Field(default_factory=list)


class FeatureFlagManager:
    """
    Feature flagging and emergency kill-switch manager.
    Supports gradual canary rollouts and instant disabling of tools, models, or experimental agents.
    """

    def __init__(self):
        self._flags: dict[str, FeatureFlag] = {
            "enable_gpu_workers": FeatureFlag(flag_key="enable_gpu_workers", enabled=True, description="Enable GPU worker pool"),
            "enable_long_horizon_workflows": FeatureFlag(flag_key="enable_long_horizon_workflows", enabled=True, description="Enable multi-step persistent workflows"),
            "enable_multi_agent_consensus": FeatureFlag(flag_key="enable_multi_agent_consensus", enabled=True, description="Enable multi-agent voting consensus"),
        }

    def set_flag(
        self,
        flag_key: str,
        enabled: bool,
        description: str = "",
        rollout_percentage: int = 100,
        target_tenants: Optional[list[str]] = None,
    ) -> FeatureFlag:
        flag = FeatureFlag(
            flag_key=flag_key,
            enabled=enabled,
            description=description,
            rollout_percentage=rollout_percentage,
            target_tenants=target_tenants or [],
        )
        self._flags[flag_key] = flag
        return flag

    def is_enabled(self, flag_key: str, tenant_id: str = "default_tenant") -> bool:
        flag = self._flags.get(flag_key)
        if not flag:
            return False
        if not flag.enabled:
            return False
        if flag.target_tenants and tenant_id not in flag.target_tenants:
            return False
        return True

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._flags.values())


feature_flags = FeatureFlagManager()
