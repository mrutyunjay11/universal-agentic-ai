from __future__ import annotations
from enum import Enum
from typing import Optional
from app.agent.models.provider import LLMProvider, OllamaProvider, DeterministicMockProvider
from app.config import settings


class ModelRole(str, Enum):
    FAST_MODEL = "FAST_MODEL"
    REASONING_MODEL = "REASONING_MODEL"
    CODING_MODEL = "CODING_MODEL"
    VISION_MODEL = "VISION_MODEL"
    VERIFICATION_MODEL = "VERIFICATION_MODEL"


class ModelRouter:
    """Selects and routes requests to appropriate LLM providers and models according to role requirements."""

    def __init__(self, default_provider: Optional[LLMProvider] = None):
        self.default_provider = default_provider or OllamaProvider(
            host=settings.ollama_host,
            default_model=settings.primary_model,
        )
        self.fast_provider = OllamaProvider(
            host=settings.ollama_host,
            default_model=settings.fast_model,
        )
        self.mock_provider = DeterministicMockProvider()

    def get_provider(self, role: ModelRole = ModelRole.REASONING_MODEL) -> LLMProvider:
        if role == ModelRole.FAST_MODEL:
            return self.fast_provider
        return self.default_provider


model_router = ModelRouter()
