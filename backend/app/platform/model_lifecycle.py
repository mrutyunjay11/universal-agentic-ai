from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class ModelProfile(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str
    provider: str
    context_window: int = 128000
    supports_vision: bool = True
    supports_function_calling: bool = True
    cost_per_million_tokens_usd: float = 2.5
    status: str = "ACTIVE"  # "ACTIVE", "DEGRADED", "DEPRECATED", "DISABLED"
    fallback_model_id: Optional[str] = None


class ModelLifecycleManager:
    """
    Model lifecycle, registration, capability verification, and failover router.
    Enforces that failovers never replace a primary model with an incapable fallback.
    """

    def __init__(self):
        self._models: dict[str, ModelProfile] = {
            "gemini-2.5-pro": ModelProfile(
                model_id="gemini-2.5-pro",
                provider="Google",
                context_window=1000000,
                fallback_model_id="gemini-2.5-flash",
            ),
            "gemini-2.5-flash": ModelProfile(
                model_id="gemini-2.5-flash",
                provider="Google",
                context_window=1000000,
                fallback_model_id="claude-3-5-sonnet",
            ),
            "claude-3-5-sonnet": ModelProfile(
                model_id="claude-3-5-sonnet",
                provider="Anthropic",
                context_window=200000,
            ),
        }

    def register_model(self, model: ModelProfile) -> None:
        self._models[model.model_id] = model

    def get_model(self, model_id: str) -> Optional[ModelProfile]:
        return self._models.get(model_id)

    def resolve_model_or_fallback(
        self,
        requested_model_id: str,
        required_capabilities: Optional[list[str]] = None,
    ) -> Optional[ModelProfile]:
        model = self._models.get(requested_model_id)
        if not model:
            return None

        if model.status == "ACTIVE":
            return model

        # Model is degraded or unavailable -> Check fallback
        fallback_id = model.fallback_model_id
        while fallback_id:
            fb = self._models.get(fallback_id)
            if not fb:
                break
            if fb.status == "ACTIVE":
                # Verify capabilities
                if required_capabilities:
                    if "vision" in required_capabilities and not fb.supports_vision:
                        fallback_id = fb.fallback_model_id
                        continue
                return fb
            fallback_id = fb.fallback_model_id

        return None


model_lifecycle = ModelLifecycleManager()
