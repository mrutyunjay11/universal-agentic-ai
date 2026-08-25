import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryType, MemoryScope


class TestMemorySecurityAndIsolation:
    @pytest.mark.asyncio
    async def test_tenant_and_project_isolation(self):
        manager = MemoryManager()
        await manager.initialize()

        # Project 1 secret convention
        await manager.remember(
            content="Project Secret: API token prefix is sk-prod-proj1-",
            memory_type=MemoryType.PROJECT,
            scope=MemoryScope.PROJECT,
            project_id="tenant_a_proj",
        )

        # Project 2
        await manager.remember(
            content="Project Secret: API token prefix is sk-test-proj2-",
            memory_type=MemoryType.PROJECT,
            scope=MemoryScope.PROJECT,
            project_id="tenant_b_proj",
        )

        # Query from Tenant B must never leak Tenant A
        tenant_b_results = await manager.retrieve(query="API token prefix", project_id="tenant_b_proj")
        assert len(tenant_b_results) >= 1
        assert "sk-test-proj2-" in tenant_b_results[0][1].content
        assert not any("sk-prod-proj1-" in r[1].content for r in tenant_b_results)

    @pytest.mark.asyncio
    async def test_user_isolation(self):
        manager = MemoryManager()
        await manager.initialize()

        # User A private preference
        await manager.remember(
            content="User prefers Python for data tasks",
            memory_type=MemoryType.USER_PREFERENCE,
            scope=MemoryScope.USER,
            user_id="user_alpha",
        )

        # User B querying should not receive User A's private memory
        user_b_results = await manager.retrieve(query="preferences", user_id="user_beta")
        assert not any("user_alpha" == r[1].user_id for r in user_b_results)
