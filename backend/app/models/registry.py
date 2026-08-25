from __future__ import annotations
from typing import Any, Optional

from app.models.base import (
    ReasoningModelProvider,
    EmbeddingProvider,
    RerankerProvider,
    ModelMetadata,
    ModelRole,
    ModelAvailability,
)
from app.models.qwen_reasoning import QwenReasoningProvider
from app.models.fallback_reasoning import FallbackReasoningProvider
from app.models.qwen_embedding import QwenEmbeddingProvider
from app.models.qwen_reranker import QwenRerankerProvider


class ModelRegistry:
    """
    Central Model Registry.
    Tracks all active, loadable, and fallback models across reasoning, embedding, and reranking roles.
    """

    def __init__(self):
        self._reasoning_providers: dict[str, ReasoningModelProvider] = {}
        self._embedding_providers: dict[str, EmbeddingProvider] = {}
        self._reranker_providers: dict[str, RerankerProvider] = {}

        # Register default approved models
        self.register_reasoning_provider("Qwen3.8-Max", QwenReasoningProvider(model_id="Qwen3.8-Max", mode="remote"))
        self.register_reasoning_provider("Qwen/Qwen3.8-2.4T-A95B", QwenReasoningProvider(model_id="Qwen/Qwen3.8-2.4T-A95B", mode="local"))
        self.register_reasoning_provider("qwen2.5-coder:32b", FallbackReasoningProvider(model_id="qwen2.5-coder:32b"))
        self.register_embedding_provider("Qwen/Qwen3-Embedding-8B", QwenEmbeddingProvider(model_id="Qwen/Qwen3-Embedding-8B"))
        self.register_reranker_provider("Qwen/Qwen3-Reranker-8B", QwenRerankerProvider(model_id="Qwen/Qwen3-Reranker-8B"))

    def register_reasoning_provider(self, model_id: str, provider: ReasoningModelProvider) -> None:
        self._reasoning_providers[model_id] = provider

    def register_embedding_provider(self, model_id: str, provider: EmbeddingProvider) -> None:
        self._embedding_providers[model_id] = provider

    def register_reranker_provider(self, model_id: str, provider: RerankerProvider) -> None:
        self._reranker_providers[model_id] = provider

    def get_reasoning_provider(self, model_id: str = "Qwen3.8-Max") -> Optional[ReasoningModelProvider]:
        return self._reasoning_providers.get(model_id)

    def get_embedding_provider(self, model_id: str = "Qwen/Qwen3-Embedding-8B") -> Optional[EmbeddingProvider]:
        return self._embedding_providers.get(model_id)

    def get_reranker_provider(self, model_id: str = "Qwen/Qwen3-Reranker-8B") -> Optional[RerankerProvider]:
        return self._reranker_providers.get(model_id)

    def list_all_models(self) -> list[dict[str, Any]]:
        models = []
        for p in self._reasoning_providers.values():
            if hasattr(p, "metadata"):
                models.append(p.metadata.model_dump())
        for p in self._embedding_providers.values():
            if hasattr(p, "metadata"):
                models.append(p.metadata.model_dump())
        for p in self._reranker_providers.values():
            if hasattr(p, "metadata"):
                models.append(p.metadata.model_dump())
        return models

    async def run_health_checks(self) -> dict[str, dict[str, Any]]:
        report: dict[str, dict[str, Any]] = {}
        for mid, p in self._reasoning_providers.items():
            status, msg = await p.health_check()
            report[mid] = {"status": status.value, "message": msg, "role": "REASONING"}
        for mid, p in self._embedding_providers.items():
            status, msg = await p.health_check()
            report[mid] = {"status": status.value, "message": msg, "role": "EMBEDDING"}
        for mid, p in self._reranker_providers.items():
            status, msg = await p.health_check()
            report[mid] = {"status": status.value, "message": msg, "role": "RERANKER"}
        return report


model_registry = ModelRegistry()
