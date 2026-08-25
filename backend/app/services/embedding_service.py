from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Optional
from functools import lru_cache

import numpy as np

from app.config import settings
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, max_size: int = 200):
        self._cache: dict[str, list[float]] = {}
        self._max_size = max_size
        self._order: list[str] = []

    def get(self, text: str) -> Optional[list[float]]:
        return self._cache.get(text)

    def set(self, text: str, vector: list[float]):
        if len(self._cache) >= self._max_size:
            oldest = self._order.pop(0)
            self._cache.pop(oldest, None)
        self._cache[text] = vector
        self._order.append(text)

    def clear(self):
        self._cache.clear()
        self._order.clear()


class EmbeddingService:
    def __init__(self):
        self._model: str = settings.embedding_model
        self._dim: int = settings.embedding_dim
        self._batch_size: int = settings.embedding_batch_size
        self._cache = EmbeddingCache(max_size=settings.embedding_cache_size)
        self._queue: asyncio.Queue[tuple[list[str], asyncio.Future]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self):
        self._running = True
        self._worker_task = asyncio.create_task(self._batch_worker())

    async def shutdown(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        uncached: list[tuple[int, str]] = []
        results: list[Optional[list[float]]] = [None] * len(texts)

        for i, text in enumerate(texts):
            cached = self._cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                uncached.append((i, text))

        if not uncached:
            return results

        for batch_start in range(0, len(uncached), self._batch_size):
            batch = uncached[batch_start : batch_start + self._batch_size]
            batch_texts = [t for _, t in batch]

            try:
                vectors = await ollama_client.embed(self._model, batch_texts)
                for (idx, text), vec in zip(batch, vectors):
                    results[idx] = vec
                    self._cache.set(text, vec)
            except Exception as e:
                logger.error("Embedding batch failed: %s", e)
                for idx, _ in batch:
                    results[idx] = [0.0] * self._dim

        return results

    async def embed_single(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0] if result else [0.0] * self._dim

    async def _batch_worker(self):
        while self._running:
            try:
                texts, future = await asyncio.wait_for(
                    self._queue.get(), timeout=2.0
                )
                try:
                    vectors = await self.embed(texts)
                    future.set_result(vectors)
                except Exception as e:
                    future.set_exception(e)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Embedding worker error: %s", e)


embedding_service = EmbeddingService()
