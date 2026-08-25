import pytest
from app.integrations.connectors.cloud import cloud_connector
from app.integrations.base import IntegrationContext


class TestCloudIntegration:
    @pytest.mark.asyncio
    async def test_instance_listing_and_metrics(self):
        ctx = IntegrationContext()
        instances = await cloud_connector.execute("list_instances", ctx)
        assert instances.status == "SUCCESS"
        assert len(instances.data) >= 1

        metrics = await cloud_connector.execute("get_metrics", ctx)
        assert metrics.status == "SUCCESS"
        assert "cpu_utilization" in metrics.data
