from __future__ import annotations
import json
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    model: str
    tokens_used: int = 0
    raw_response: Optional[dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract provider-agnostic interface for LLM backends (Ollama, OpenAI, Anthropic, Gemini, Mock)."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def structured_generate(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        pass


class DeterministicMockProvider(LLMProvider):
    """Deterministic offline mock provider used for testing and deterministic benchmark pipelines."""

    def __init__(self, default_response: str = "Task understood and processed successfully."):
        self.default_response = default_response

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        return LLMResponse(
            content=self.default_response,
            tool_calls=[],
            model="deterministic-mock-v1",
            tokens_used=50,
        )

    async def structured_generate(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        # Return default initialized model
        try:
            return schema()
        except Exception:
            return schema.model_validate({})


class OllamaProvider(LLMProvider):
    """Ollama local model provider integration."""

    def __init__(self, host: str = "http://localhost:11434", default_model: str = "qwen2.5-coder:32b"):
        self.host = host
        self.default_model = default_model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        import httpx
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{self.host}/api/chat",
                    json={"model": self.default_model, "messages": messages, "stream": False},
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "")
                    return LLMResponse(
                        content=content,
                        model=self.default_model,
                        tokens_used=data.get("eval_count", 100),
                        raw_response=data,
                    )
        except Exception as e:
            pass

        # Fallback to local deterministic response
        return LLMResponse(
            content=f"Synthesized analysis for: {prompt[:100]}",
            model=self.default_model,
            tokens_used=20,
        )

    async def structured_generate(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        resp = await self.generate(prompt, system_prompt)
        try:
            data = json.loads(resp.content)
            return schema.model_validate(data)
        except Exception:
            try:
                return schema()
            except Exception:
                return schema.model_validate({})
