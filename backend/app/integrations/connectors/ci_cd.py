from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class CICDConnector(Integration):
    name = "ci_cd"
    provider = "CICDGateway"
    capabilities = ["trigger_pipeline", "get_pipeline_status", "cancel_pipeline", "get_artifacts"]
    auth_methods = ["api_token", "webhook_secret"]

    def __init__(self):
        self._connected = True

    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        self._connected = True
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.CONNECTED, latency_ms=10)
        return True

    async def disconnect(self, context: IntegrationContext) -> bool:
        self._connected = False
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.DISCONNECTED)
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 12}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data: Any = None
        if action == "trigger_pipeline":
            data = {"pipeline_id": "pipe_9901", "ref": kwargs.get("branch", "main"), "status": "RUNNING"}
        elif action == "get_pipeline_status":
            data = {"pipeline_id": kwargs.get("pipeline_id", "pipe_9901"), "status": "SUCCESS", "duration_s": 45}
        else:
            data = {"action": action, "status": "OK"}

        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=15,
        )


ci_cd_connector = CICDConnector()
