import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryType, MemoryScope


class TestUserMemory:
    @pytest.mark.asyncio
    async def test_user_preferences_and_forgetting(self):
        manager = MemoryManager()
        await manager.initialize()

        rec = await manager.remember(
            content="User prefers succinct code explanations with type annotations",
            memory_type=MemoryType.USER_PREFERENCE,
            scope=MemoryScope.USER,
            user_id="user_alice",
        )

        # Retrieve preference for Alice
        results = await manager.retrieve(query="code explanation style", user_id="user_alice")
        assert len(results) >= 1
        assert "type annotations" in results[0][1].content

        # Explicit forget
        deleted = await manager.forget(rec.id)
        assert deleted is True

        after_del = await manager.get(rec.id)
        assert after_del is None
