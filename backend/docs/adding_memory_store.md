# Guide: Adding a Custom Memory Storage Backend

To integrate a new storage backend (e.g. Qdrant, PostgreSQL pgvector, Pinecone, Redis):

1. Subclass `MemoryStore` from `app.memory.base`:
```python
from app.memory.base import MemoryStore
from app.memory.models import MemoryRecord, MemoryType, MemoryScope

class CustomVectorStore(MemoryStore):
    async def initialize(self) -> None:
        ...
    async def insert(self, record: MemoryRecord) -> MemoryRecord:
        ...
    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        ...
    async def update(self, record: MemoryRecord) -> MemoryRecord:
        ...
    async def delete(self, memory_id: str) -> bool:
        ...
    async def search(self, query: str, limit: int = 10, ...) -> list[MemoryRecord]:
        ...
    async def list_all(self, limit: int = 100, ...) -> list[MemoryRecord]:
        ...
    async def count(self, ...) -> int:
        ...
    async def clear(self) -> None:
        ...
```

2. Register your custom store when instantiating `MemoryManager`:
```python
manager = MemoryManager(store=CustomVectorStore())
```
