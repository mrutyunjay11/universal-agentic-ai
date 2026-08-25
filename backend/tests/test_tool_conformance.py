from __future__ import annotations
import pytest
from app.tools.registry import tool_registry
from app.tools.base import BaseTool, ToolCategory, ToolContext
from app.tools.permissions import PermissionTier
from app.tools.audit import redact_secrets


@pytest.mark.asyncio
class TestToolConformance:
    """
    Universal Conformance Test Suite.
    Ensures every tool registered across all 19 categories adheres to standard contracts.
    """
    async def test_all_tools_are_base_tool_instances(self):
        await tool_registry.discover_tools()
        assert len(tool_registry.tools) > 0, "No tools registered in ecosystem"

        for name, tool in tool_registry.tools.items():
            assert isinstance(tool, BaseTool), f"Tool {name} does not inherit from BaseTool"
            assert tool.metadata.name == name, f"Tool name mismatch: {tool.metadata.name} != {name}"
            assert isinstance(tool.metadata.category, ToolCategory), f"Tool {name} has invalid category"
            assert isinstance(tool.metadata.permission, PermissionTier), f"Tool {name} has invalid permission"
            assert tool.metadata.timeout > 0, f"Tool {name} must have a positive timeout"

    async def test_tool_schemas_export_validity(self):
        await tool_registry.discover_tools()
        openai_schemas = tool_registry.get_schemas(format="openai")
        assert len(openai_schemas) == len(tool_registry.tools)

        for s in openai_schemas:
            assert s.get("type") == "function"
            assert "function" in s
            func = s["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    async def test_secret_redaction_conformance(self):
        raw_secret_data = {
            "api_key": "sk-1234567890abcdef12345678",
            "db_url": "postgres://user:supersecretpass@localhost:5432/db",
            "nested": {"token": "ghp_abcdefghijklmnopqrstuvwxyz1234567890"},
        }
        redacted = redact_secrets(raw_secret_data)
        assert "supersecretpass" not in str(redacted)
        assert "sk-1234567890" not in str(redacted)
        assert "ghp_" not in str(redacted)
        assert "***REDACTED***" in str(redacted)

    async def test_permission_denial_gating(self):
        await tool_registry.discover_tools()
        # Find a tool requiring EXECUTE or SYSTEM
        sys_tools = [t for t in tool_registry.tools.values() if t.metadata.permission in (PermissionTier.EXECUTE, PermissionTier.SYSTEM)]
        if sys_tools:
            target_tool = sys_tools[0]
            # Try running with only READ permission granted
            ctx = ToolContext(permission_granted=PermissionTier.READ)
            res = await tool_registry.execute(target_tool.metadata.name, {}, ctx)
            assert not res.success, f"Tool {target_tool.metadata.name} should fail with insufficient permission"
            assert res.error.type.value == "permission_denied"
