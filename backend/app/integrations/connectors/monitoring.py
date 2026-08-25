from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class MonitoringConnector(Integration):
    name = "monitoring"
    provider = "ObservabilityGateway"
    capabilities = ["query_logs", "query_metrics", "get_alert", "acknowledge_alert", "create_incident"]
    auth_methods = ["api_key", "bearer_token"]

    def __init__(self):
        self._connected = True

    async def connect(self, context: IntegrationContext, **kwargs) -> bool:
        self._connected = True
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.CONNECTED, latency_ms=8)
        return True

    async def disconnect(self, context: IntegrationContext) -> bool:
        self._connected = False
        health_monitor.record_health(self.name, self.provider, IntegrationStatus.DISCONNECTED)
        return True

    async def health_check(self) -> dict[str, Any]:
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 9}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data: Any = None
        if action == "query_logs":
            data = {"matches": ["2026-08-25 ERROR 500 in /api/payment - Gateway Timeout", "2026-08-25 INFO Retrying..."], "count": 2}
        elif action == "get_alert":
            data = {"alert_id": "alt_882", "severity": "HIGH", "name": "Payment Service Latency Spike", "status": "TRIGGERED"}
        elif action == "create_incident":
            data = {"incident_id": "inc_441", "title": kwargs.get("title", "Service Degradation"), "severity": "HIGH", "status": "INVESTIGATING"}
        else:
            data = {"action": action, "status": "OK"}

        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=14,
        )


monitoring_connector = MonitoringConnector()
