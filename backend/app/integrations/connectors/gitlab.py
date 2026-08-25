from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class GitLabConnector(Integration):
    name = "gitlab"
    provider = "GitLab"
    capabilities = ["list_projects", "create_merge_request", "trigger_pipeline", "get_pipeline_status"]
    auth_methods = ["oauth2", "personal_access_token"]

    def __init__(self):
        self._connected = True

    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        self._connected = True
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.CONNECTED, latency_ms=18)
        return True

    async def disconnect(self, context: IntegrationContext) -> bool:
        self._connected = False
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.DISCONNECTED)
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 20}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data = {"gitlab_action": action, "project": kwargs.get("project_id", "1234"), "status": "COMPLETED"}
        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=22,
        )


gitlab_connector = GitLabConnector()
