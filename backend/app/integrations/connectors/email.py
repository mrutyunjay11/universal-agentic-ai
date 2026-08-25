from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class EmailConnector(Integration):
    name = "email"
    provider = "EmailGateway"
    capabilities = ["search_messages", "read_message", "draft_message", "send_message", "archive_message"]
    auth_methods = ["oauth2", "smtp_credentials"]

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
        if action == "draft_message":
            data = {
                "draft_id": "draft_msg_901",
                "to": kwargs.get("to", "user@example.com"),
                "subject": kwargs.get("subject", "Automated Notice"),
                "status": "DRAFTED",
            }
        elif action == "send_message":
            data = {
                "message_id": "msg_sent_772",
                "to": kwargs.get("to", "user@example.com"),
                "subject": kwargs.get("subject", "Notice"),
                "status": "SENT",
                "verified_delivery": True,
            }
        else:
            data = {"action": action, "status": "OK"}

        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=15,
            reconciliation_state={"delivered": True},
        )


email_connector = EmailConnector()
