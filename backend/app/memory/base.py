from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus


class MemoryStore(ABC):
    """
    Abstract interface for pluggable memory storage backends (SQLite, Vector, Hybrid, etc.).
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initializes database schema, indexes, or connections."""
        pass

    @abstractmethod
    async def insert(self, record: MemoryRecord) -> MemoryRecord:
        """Inserts a new memory record."""
        pass

    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieves a memory record by its unique ID."""
        pass

    @abstractmethod
    async def update(self, record: MemoryRecord) -> MemoryRecord:
        """Updates an existing memory record."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Deletes a memory record by ID."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        scope: Optional[MemoryScope] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_confidence: float = 0.0,
        include_stale: bool = False,
    ) -> list[MemoryRecord]:
        """Searches memories matching criteria with keyword and/or semantic filters."""
        pass

    @abstractmethod
    async def list_all(
        self,
        limit: int = 100,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        """Lists records with optional scope filtering."""
        pass

    @abstractmethod
    async def count(
        self,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """Counts total records matching criteria."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clears all records in the store (useful for testing and reset)."""
        pass


@runtime_checkable
class EmbeddingProvider(Protocol):
    """
    Protocol for embedding providers (Ollama, OpenAI, FastEmbed, DeterministicMock, etc.).
    """
    dimension: int

    async def embed_text(self, text: str) -> list[float]:
        """Generates embedding vector for a single text string."""
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates embedding vectors for multiple text strings in batch."""
        ...
