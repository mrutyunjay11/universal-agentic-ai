from __future__ import annotations
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier


@pytest.mark.asyncio
class TestToolRegistry:
    async def test_auto_discovery_and_health_check(self):
        await tool_registry.discover_tools()
        health = tool_registry.health_check()
        assert health["total_tools"] > 0
        assert health["available_tools"] > 0
        assert len(health["categories"]) >= 10
        assert "file" in health["categories"]
        assert "code" in health["categories"]
        assert "verification" in health["categories"]
        assert "math" in health["categories"]

    async def test_category_filtering(self):
        await tool_registry.discover_tools()
        file_tools = tool_registry.list_tools(ToolCategory.FILE)
        assert len(file_tools) >= 10
        for t in file_tools:
            assert t.metadata.category == ToolCategory.FILE

        math_tools = tool_registry.list_tools(ToolCategory.MATH)
        assert len(math_tools) >= 5
        for t in math_tools:
            assert t.metadata.category == ToolCategory.MATH

    async def test_get_nonexistent_tool(self):
        res = await tool_registry.execute("non_existent_tool_12345", {})
        assert not res.success
        assert res.error.type.value == "not_found"
