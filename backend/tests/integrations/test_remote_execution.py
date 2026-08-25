import pytest
from app.integrations.connectors.remote_exec import remote_exec_connector
from app.integrations.base import IntegrationContext


class TestRemoteExecution:
    @pytest.mark.asyncio
    async def test_remote_ssh_command_execution(self):
        ctx = IntegrationContext()
        res = await remote_exec_connector.execute("execute_command", ctx, command="uname -a")
        assert res.status == "SUCCESS"
        assert "Linux" in res.data["stdout"]
        assert res.data["exit_code"] == 0
