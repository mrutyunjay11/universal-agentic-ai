import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryType


class TestProceduralMemory:
    @pytest.mark.asyncio
    async def test_procedural_memory_storage_and_retrieval(self):
        manager = MemoryManager()
        await manager.initialize()

        await manager.remember(
            content="To deploy to staging: 1. git pull origin main 2. uv run pytest 3. docker build -t app:staging .",
            memory_type=MemoryType.PROCEDURAL,
            project_id="proj_staging",
            confidence=0.95,
            importance=0.9,
            tags=["deployment", "staging", "docker"],
        )

        res = await manager.retrieve(query="how to deploy to staging", project_id="proj_staging")
        assert len(res) >= 1
        assert "docker build -t app:staging" in res[0][1].content
