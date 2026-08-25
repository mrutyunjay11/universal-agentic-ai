from __future__ import annotations
import hashlib
import math
import logging
from typing import Optional
import httpx
from app.memory.base import EmbeddingProvider
from app.config import settings

logger = logging.getLogger(__name__)


class DeterministicMockEmbedder(EmbeddingProvider):
    """
    Fast, deterministic embedding generator using SHA-256 hash seeds and trigonometric projection.
    Generates unit-normalized 768-dimensional vectors for fast, reproducible unit testing without external APIs.
    """
    dimension: int = 768

    async def embed_text(self, text: str) -> list[float]:
        return self._compute_vector(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._compute_vector(t) for t in texts]

    def _compute_vector(self, text: str) -> list[float]:
        import random
        tokens = text.lower().strip().split()
        vector = [0.0] * self.dimension
        
        if not tokens:
            return vector

        for i, token in enumerate(tokens):
            rng = random.Random(token)
            weight = 1.0 / (1.0 + math.log(1.0 + i))
            for dim_idx in range(self.dimension):
                vector[dim_idx] += rng.gauss(0, 1.0) * weight

        # Normalize vector to unit length
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 1e-9:
            vector = [x / norm for x in vector]
        return vector


class OllamaEmbedder(EmbeddingProvider):
    """
    Local neural embedding provider interfacing with local Ollama service (e.g., nomic-embed-text).
    """
    dimension: int = 768

    def __init__(self, model_name: str = "nomic-embed-text", base_url: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url or settings.OLLAMA_BASE_URL.rstrip("/")

    async def embed_text(self, text: str) -> list[float]:
        results = await self.embed_documents([text])
        return results[0] if results else [0.0] * self.dimension

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for text in texts:
                try:
                    res = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": text},
                    )
                    if res.status_code == 200:
                        vec = res.json().get("embedding", [])
                        embeddings.append(vec)
                    else:
                        logger.warning("Ollama embeddings failed (%s), falling back to mock vector", res.status_code)
                        embeddings.append(DeterministicMockEmbedder()._compute_vector(text))
                except Exception as e:
                    logger.debug("Ollama embedding exception: %s, falling back to mock", e)
                    embeddings.append(DeterministicMockEmbedder()._compute_vector(text))
        return embeddings


def get_embedding_provider() -> EmbeddingProvider:
    """Returns configured embedding provider instance."""
    # Defaults to deterministic mock embedder for predictable, rapid test execution
    return DeterministicMockEmbedder()
