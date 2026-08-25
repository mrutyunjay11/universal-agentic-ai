from __future__ import annotations
import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url: str = settings.ollama_host
        self._max_retries: int = 3
        self._retry_delay: float = 1.0

    async def ensure_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(120.0, connect=10.0),
            )

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[list[int]] = None,
        options: Optional[dict[str, Any]] = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        await self.ensure_client()
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": options or {},
        }
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await self._client.post("/api/generate", json=payload)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    "Ollama generate attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise RuntimeError(f"Ollama generate failed after {self._max_retries} attempts: {last_error}")

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[list[int]] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        await self.ensure_client()
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": options or {},
        }
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                async with self._client.stream(
                    "POST", "/api/generate", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.strip():
                            yield json.loads(line)
                return
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    "Ollama stream attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Ollama stream failed after {self._max_retries} attempts: {last_error}"
        )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = False,
        options: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        await self.ensure_client()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options or {},
        }

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = await self._client.post("/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    "Ollama chat attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Ollama chat failed after {self._max_retries} attempts: {last_error}"
        )

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        options: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        await self.ensure_client()
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options or {},
        }

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                async with self._client.stream(
                    "POST", "/api/chat", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.strip():
                            yield json.loads(line)
                return
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    "Ollama chat stream attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    e,
                )
                if attempt < self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Ollama chat stream failed after {self._max_retries} attempts: {last_error}"
        )

    async def embed(
        self, model: str, input_texts: list[str]
    ) -> list[list[float]]:
        await self.ensure_client()
        payload = {"model": model, "input": input_texts}

        try:
            resp = await self._client.post("/api/embed", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("embeddings", [])
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.error("Ollama embed failed: %s", e)
            raise

    async def is_available(self) -> bool:
        try:
            await self.ensure_client()
            resp = await self._client.get("/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


ollama_client = OllamaClient()
