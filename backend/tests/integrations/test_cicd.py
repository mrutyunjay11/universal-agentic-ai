import pytest
from app.integrations.connectors.ci_cd import ci_cd_connector
from app.integrations.base import IntegrationContext


class TestCICDIntegration:
    @pytest.mark.asyncio
    async def test_trigger_and_poll_pipeline(self):
        ctx = IntegrationContext()
        triggered = await ci_cd_connector.execute("trigger_pipeline", ctx, branch="main")
        assert triggered.status == "SUCCESS"
        assert triggered.data["status"] == "RUNNING"

        status = await ci_cd_connector.execute("get_pipeline_status", ctx, pipeline_id=triggered.data["pipeline_id"])
        assert status.status == "SUCCESS"
        assert status.data["status"] == "SUCCESS"
