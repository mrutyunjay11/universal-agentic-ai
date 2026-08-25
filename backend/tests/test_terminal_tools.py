from __future__ import annotations
import tempfile
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.mark.asyncio
class TestTerminalTools:
    async def test_execute_terminal_safe_command(self):
        ctx = ToolContext(permission_granted=PermissionTier.SYSTEM)
        res = await tool_registry.execute("execute_terminal", {"command": "echo 'Hello Universal Agent'"}, ctx)
        assert res.success
        assert "Hello Universal Agent" in res.output["stdout"]
        assert res.output["return_code"] == 0

    async def test_background_process_lifecycle(self):
        ctx = ToolContext(permission_granted=PermissionTier.SYSTEM)
        # Start background sleep process
        start_res = await tool_registry.execute("run_background_process", {"command": "sleep 10"}, ctx)
        assert start_res.success
        pid = start_res.output["process_id"]

        # Check status
        status_res = await tool_registry.execute("get_process_status", {"process_id": pid}, ctx)
        assert status_res.success
        assert status_res.output["status"] == "running"

        # Kill process
        kill_res = await tool_registry.execute("kill_process", {"process_id": pid}, ctx)
        assert kill_res.success
        assert kill_res.output["status"] == "terminated"

    async def test_terminal_denied_command(self):
        ctx = ToolContext(permission_granted=PermissionTier.SYSTEM)
        res = await tool_registry.execute("execute_terminal", {"command": "rm -rf /"}, ctx)
        assert not res.success
        assert res.error.type.value == "security_violation"
