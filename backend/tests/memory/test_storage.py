import pytest
from app.memory.stores.sqlite import SQLiteMemoryStore
from app.memory.stores.vector import VectorMemoryStore
from app.memory.stores.hybrid import HybridMemoryStore
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus


class TestMemoryStorageBackends:
    @pytest.mark.asyncio
    async def test_sqlite_store_crud(self):
        store = SQLiteMemoryStore(":memory:")
        await store.initialize()

        rec = MemoryRecord(
            content="SQLite is ACID compliant",
            memory_type=MemoryType.FACT,
            project_id="proj_1",
            verification_status=VerificationStatus.VERIFIED,
            tags=["database", "sql"],
        )
        saved = await store.insert(rec)
        assert saved.id == rec.id

        fetched = await store.get(rec.id)
        assert fetched is not None
        assert fetched.content == "SQLite is ACID compliant"
        assert fetched.tags == ["database", "sql"]

        fetched.content = "SQLite is lightweight and ACID compliant"
        updated = await store.update(fetched)
        assert updated.content == "SQLite is lightweight and ACID compliant"

        results = await store.search(query="ACID", project_id="proj_1")
        assert len(results) >= 1
        assert results[0].id == rec.id

        deleted = await store.delete(rec.id)
        assert deleted is True
        assert await store.get(rec.id) is None

    @pytest.mark.asyncio
    async def test_vector_store_crud(self):
        store = VectorMemoryStore()
        await store.initialize()

        rec = MemoryRecord(
            content="Quantum computing uses qubits and superposition",
            memory_type=MemoryType.SEMANTIC,
        )
        await store.insert(rec)

        res = await store.search(query="qubits superposition", limit=5)
        assert len(res) >= 1
        assert res[0].id == rec.id

        await store.delete(rec.id)
        assert await store.get(rec.id) is None

    @pytest.mark.asyncio
    async def test_hybrid_store_operations(self):
        store = HybridMemoryStore(
            sqlite_store=SQLiteMemoryStore(":memory:"),
            vector_store=VectorMemoryStore(),
        )
        await store.initialize()

        rec = MemoryRecord(
            content="Asyncio event loop coordinates non-blocking coroutines",
            memory_type=MemoryType.SEMANTIC,
            tags=["asyncio", "python"],
        )
        await store.insert(rec)

        found = await store.search(query="coroutines", tags=["asyncio"])
        assert len(found) >= 1
        assert "coroutines" in found[0].content

        await store.clear()
        assert await store.count() == 0
