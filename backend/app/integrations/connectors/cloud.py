from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class CloudConnector(Integration):
    name = "cloud"
    provider = "UniversalCloudGateway"
    capabilities = ["list_instances", "start_instance", "stop_instance", "get_metrics", "query_logs"]
    auth_methods = ["iam_role", "service_account"]

    def __init__(self):
        self._connected = True

    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        self._connected = True
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.CONNECTED, latency_ms=15)
        return True

    async def disconnect(self, context: IntegrationContext) -> bool:
        self._connected = False
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.DISCONNECTED)
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 16}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data: Any = None
        if action == "list_instances":
            data = [{"instance_id": "i-0a8172bc", "type": "t4g.xlarge", "state": "RUNNING"}]
        elif action == "get_metrics":
            data = {"cpu_utilization": 24.5, "memory_used_pct": 42.0}
        else:
            data = {"action": action, "status": "OK"}

        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=20,
        )


cloud_connector = CloudConnector()
