import pytest
from app.platform.retention import DataRetentionManager


class TestRetentionAndPrivacy:
    def test_user_privacy_forget_and_export(self):
        drm = DataRetentionManager()

        forget_res = drm.forget_user_memory("user_alice", tenant_id="tenant_acme")
        assert forget_res["status"] == "PURGED"
        assert forget_res["user_id"] == "user_alice"

        export_res = drm.export_user_data("user_alice", tenant_id="tenant_acme")
        assert export_res["status"] == "EXPORT_READY"
        assert "tasks_count" in export_res
