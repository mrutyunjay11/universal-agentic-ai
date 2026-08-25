import pytest
from app.integrations.connectors.storage import storage_connector
from app.integrations.base import IntegrationContext


class TestStorageIntegration:
    @pytest.mark.asyncio
    async def test_file_upload_list_and_delete(self):
        ctx = IntegrationContext()
        upload = await storage_connector.execute("upload_file", ctx, key="reports/q3_summary.pdf")
        assert upload.status == "SUCCESS"
        assert upload.data["status"] == "UPLOADED"

        files = await storage_connector.execute("list_files", ctx)
        assert files.status == "SUCCESS"
        assert len(files.data) >= 1

        delete = await storage_connector.execute("delete_file", ctx, key="reports/q3_summary.pdf")
        assert delete.status == "SUCCESS"
        assert delete.data["deleted"] is True
