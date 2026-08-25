import pytest
from app.integrations.connectors.monitoring import monitoring_connector
from app.integrations.base import IntegrationContext


class TestMonitoringIntegration:
    @pytest.mark.asyncio
    async def test_alert_query_and_incident_creation(self):
        ctx = IntegrationContext()
        alert = await monitoring_connector.execute("get_alert", ctx)
        assert alert.status == "SUCCESS"
        assert alert.data["severity"] == "HIGH"

        inc = await monitoring_connector.execute("create_incident", ctx, title="High Error Rate in Checkout")
        assert inc.status == "SUCCESS"
        assert inc.data["status"] == "INVESTIGATING"
