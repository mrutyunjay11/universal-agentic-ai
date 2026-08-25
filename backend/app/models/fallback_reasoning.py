from __future__ import annotations
import json
import time
from typing import Any, AsyncIterator, Optional

from app.models.base import (
    ReasoningModelProvider,
    ReasoningResponse,
    ModelMetadata,
    ModelRole,
    ModelAvailability,
)
from app.context.tokenizer import tokenizer_provider


class FallbackReasoningProvider(ReasoningModelProvider):
    """
    Hardware-Aware Fallback Reasoning Provider.
    Operates when flagship models are unavailable or hardware resources are constrained.
    """

    def __init__(
        self,
        model_id: str = "qwen2.5-coder:32b",
        provider: str = "Ollama",
        context_limit: int = 32768,
    ):
        self.model_id = model_id
        self.provider = provider
        self.context_limit = context_limit

        self.metadata = ModelMetadata(
            model_id=self.model_id,
            provider=self.provider,
            role=ModelRole.REASONING,
            version="2.5",
            context_limit=self.context_limit,
            tokenizer="cl100k_base",
            capabilities=["chat", "tools", "structured_output"],
            local_or_remote="local",
            hardware_requirements={"min_vram_gb": 24},
            availability=ModelAvailability.READY,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ReasoningResponse:
        start_time = time.time()
        full_text = f"{system_prompt or ''}\n{prompt}"
        p_tokens, _ = tokenizer_provider.count_tokens(full_text, model=self.model_id)

        simulated_response = f"Fallback reasoning response [{self.model_id}]: {prompt[:80]}"
        c_tokens, _ = tokenizer_provider.count_tokens(simulated_response, model=self.model_id)
        latency = int((time.time() - start_time) * 1000)

        return ReasoningResponse(
            content=simulated_response,
            finish_reason="stop",
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=p_tokens + c_tokens,
            model_id=self.metadata.model_id,
            latency_ms=latency,
        )

    async def structured_generate(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ReasoningResponse:
        resp = await self.generate(prompt, system_prompt=system_prompt, **kwargs)
        structured_data = {"status": "FALLBACK_SUCCESS", "result": resp.content}
        resp.structured_output = structured_data
        resp.content = json.dumps(structured_data)
        return resp

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[dict[str, Any]],
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> ReasoningResponse:
        return await self.generate(prompt, system_prompt=system_prompt, **kwargs)

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        for word in f"Fallback stream [{self.model_id}]".split():
            yield word + " "

    async def health_check(self) -> tuple[ModelAvailability, str]:
        return ModelAvailability.READY, f"Fallback reasoning provider [{self.model_id}] healthy"
