# Guide: Adding a Custom Embedding Provider

To add a new embedding provider (e.g. OpenAI, Cohere, HuggingFace FastEmbed):

1. Implement the `EmbeddingProvider` protocol from `app.memory.base`:
```python
from app.memory.base import EmbeddingProvider

class CustomEmbedder(EmbeddingProvider):
    dimension: int = 1536

    async def embed_text(self, text: str) -> list[float]:
        # Return 1D float vector of length `dimension`
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Return batch of 1D float vectors
        ...
```

2. Pass your custom embedder to `MemoryManager`:
```python
manager = MemoryManager(embedder=CustomEmbedder())
```
