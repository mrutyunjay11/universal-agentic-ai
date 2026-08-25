import pytest
import asyncio
from app.integrations.connectors.storage import storage_connector
from app.integrations.base import IntegrationContext


class TestConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_connector_operations(self):
        ctx = IntegrationContext()

        tasks = [
            storage_connector.execute("upload_file", ctx, key=f"chunk_{i}.dat")
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(r.status == "SUCCESS" for r in results)
