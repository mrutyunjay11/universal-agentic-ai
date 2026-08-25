import pytest
from app.integrations.connectors.github import github_connector
from app.integrations.base import IntegrationContext


class TestIdempotency:
    @pytest.mark.asyncio
    async def test_idempotent_connector_execution(self):
        ctx = IntegrationContext(
            user_id="user_test",
            idempotency_key="idemp_key_99812",
        )

        res1 = await github_connector.execute("create_pull_request", ctx, title="Feature Branch PR")
        assert res1.status == "SUCCESS"
        assert res1.idempotency_key == "idemp_key_99812"

        # Re-running with same idempotency key
        res2 = await github_connector.execute("create_pull_request", ctx, title="Feature Branch PR")
        assert res2.status == "SUCCESS"
        assert res2.idempotency_key == "idemp_key_99812"
