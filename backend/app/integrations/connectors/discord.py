from __future__ import annotations
from typing import Any
from app.integrations.base import Integration, IntegrationContext, IntegrationResult, IntegrationStatus
from app.integrations.health import health_monitor


class DiscordConnector(Integration):
    name = "discord"
    provider = "Discord"
    capabilities = ["read_channel", "send_message"]
    auth_methods = ["bot_token", "webhook_url"]

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
        return {"connector": self.name, "status": "CONNECTED", "latency_ms": 11}

    async def execute(self, action: str, context: IntegrationContext, **kwargs) -> IntegrationResult:
        data = {"discord_action": action, "channel_id": kwargs.get("channel_id", "ch_123"), "status": "SENT"}
        return IntegrationResult(
            integration_name=self.name,
            action=action,
            status="SUCCESS",
            data=data,
            duration_ms=12,
        )


discord_connector = DiscordConnector()
