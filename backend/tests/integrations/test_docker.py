import pytest
from app.integrations.connectors.docker import docker_connector
from app.integrations.base import IntegrationContext


class TestDockerIntegration:
    @pytest.mark.asyncio
    async def test_container_lifecycle_and_logs(self):
        ctx = IntegrationContext()
        container = await docker_connector.execute("run_container", ctx, image="python:3.12-slim")
        assert container.status == "SUCCESS"
        assert container.data["status"] == "RUNNING"

        logs = await docker_connector.execute("read_logs", ctx, container_id=container.data["container_id"])
        assert logs.status == "SUCCESS"
        assert "INFO" in logs.data["logs"]
