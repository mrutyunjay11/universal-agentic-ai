from __future__ import annotations
from typing import Any, Optional

from app.models.base import ReasoningModelProvider, ModelAvailability
from app.models.registry import model_registry, ModelRegistry


class ModelRouter:
    """
    Hardware and Task-Aware Model Router.
    Routes inference requests to the optimal reasoning provider (Flagship, Local Flagship, or Hardware Fallback).
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or model_registry
        self.primary_model_id = "Qwen3.8-Max"
        self.local_flagship_id = "Qwen/Qwen3.8-2.4T-A95B"
        self.fallback_model_id = "qwen2.5-coder:32b"

    async def route_reasoning(
        self,
        task_type: str = "GENERAL",
        prefer_local: bool = False,
        required_capabilities: Optional[list[str]] = None,
    ) -> tuple[ReasoningModelProvider, str]:
        # 1. If local preferred, evaluate Local Flagship
        if prefer_local:
            local_p = self.registry.get_reasoning_provider(self.local_flagship_id)
            if local_p:
                status, _ = await local_p.health_check()
                if status == ModelAvailability.READY:
                    return local_p, self.local_flagship_id

            # Fallback local
            fb_p = self.registry.get_reasoning_provider(self.fallback_model_id)
            if fb_p:
                return fb_p, self.fallback_model_id

        # 2. Try Primary Flagship (Qwen3.8-Max)
        primary_p = self.registry.get_reasoning_provider(self.primary_model_id)
        if primary_p:
            status, _ = await primary_p.health_check()
            if status == ModelAvailability.READY:
                return primary_p, self.primary_model_id

        # 3. Fallback to secondary model
        fb_p = self.registry.get_reasoning_provider(self.fallback_model_id)
        if fb_p:
            return fb_p, self.fallback_model_id

        raise RuntimeError("No operational reasoning model provider found in registry")


model_router = ModelRouter()
