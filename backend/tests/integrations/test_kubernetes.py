import pytest
from app.integrations.connectors.kubernetes import kubernetes_connector
from app.integrations.base import IntegrationContext


class TestKubernetesIntegration:
    @pytest.mark.asyncio
    async def test_pod_listing_and_manifest_application(self):
        ctx = IntegrationContext()
        pods = await kubernetes_connector.execute("list_pods", ctx, namespace="prod")
        assert pods.status == "SUCCESS"
        assert len(pods.data) >= 1

        applied = await kubernetes_connector.execute(
            "apply_manifest",
            ctx,
            resource="Deployment/agent-api",
        )
        assert applied.status == "SUCCESS"
        assert applied.data["applied"] is True
