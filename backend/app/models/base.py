from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Optional
from pydantic import BaseModel, Field


class ModelRole(str, Enum):
    REASONING = "REASONING"
    EMBEDDING = "EMBEDDING"
    RERANKER = "RERANKER"
    FAST = "FAST"
    VISION = "VISION"
    VERIFICATION = "VERIFICATION"


class ModelAvailability(str, Enum):
    READY = "READY"
    LOADABLE = "LOADABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    HARDWARE_INSUFFICIENT = "HARDWARE_INSUFFICIENT"


class ModelMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str
    provider: str
    role: ModelRole = ModelRole.REASONING
    version: str = "1.0.0"
    context_limit: int = 32768
    tokenizer: str = "cl100k_base"
    capabilities: list[str] = Field(default_factory=lambda: ["chat", "tools", "structured_output"])
    local_or_remote: str = "remote"  # "local" or "remote"
    hardware_requirements: dict[str, Any] = Field(default_factory=dict)
    availability: ModelAvailability = ModelAvailability.READY


class ReasoningResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    content: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    structured_output: Optional[dict[str, Any]] = None
    finish_reason: str = "stop"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model_id: str = ""
    latency_ms: int = 0


class ReasoningModelProvider(ABC):
    """Abstract interface for LLM reasoning backends."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ReasoningResponse:
        pass

    @abstractmethod
    async def structured_generate(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ReasoningResponse:
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ReasoningResponse:
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def health_check(self) -> tuple[ModelAvailability, str]:
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for semantic embedding models."""

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        pass

    @abstractmethod
    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    async def health_check(self) -> tuple[ModelAvailability, str]:
        pass


class RerankerProvider(ABC):
    """Abstract interface for cross-attention reranking models."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def health_check(self) -> tuple[ModelAvailability, str]:
        pass
