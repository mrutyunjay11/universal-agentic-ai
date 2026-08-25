import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryType, MemoryScope


class TestProjectMemory:
    @pytest.mark.asyncio
    async def test_project_memory_lifecycle(self):
        manager = MemoryManager()
        await manager.initialize()

        # Remember project facts
        rec = await manager.remember(
            content="Project build command is 'npm run build:prod'",
            memory_type=MemoryType.PROJECT,
            scope=MemoryScope.PROJECT,
            project_id="proj_frontend",
            tags=["build", "npm"],
        )
        assert rec.project_id == "proj_frontend"

        # Query project memory
        found = await manager.retrieve(query="build command", project_id="proj_frontend")
        assert len(found) >= 1
        assert "npm run build:prod" in found[0][1].content

        # Query from different project should not return this memory
        other_found = await manager.retrieve(query="build command", project_id="proj_backend")
        assert not any(r[1].id == rec.id for r in other_found)
