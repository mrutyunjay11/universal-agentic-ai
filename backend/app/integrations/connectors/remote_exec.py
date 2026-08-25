from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class RemoteExecutionConnector(Integration):
    name = "remote_exec"
    provider = "RemoteHostSSH"
    capabilities = ["connect_host", "execute_command", "upload_file", "download_file", "disconnect_host"]
    auth_methods = ["ssh_key", "certificate"]

    def __init__(self):
        self._connected = True

    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        self._connected = True
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.CONNECTED, latency_ms=30)
        return True

    async def disconnect(self, context: IntegrationContext) -> bool:
        self._connected = False
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.DISCONNECTED)
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 32}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data: Any = None
        if action == "execute_command":
            cmd = kwargs.get("command", "uname -a")
            data = {"command": cmd, "stdout": "Linux node-cluster-01 5.15.0-generic #88 SMP x86_64", "exit_code": 0}
        else:
            data = {"action": action, "status": "OK"}

        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=40,
        )


remote_exec_connector = RemoteExecutionConnector()
