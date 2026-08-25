import pytest
from app.platform.disaster_recovery import DisasterRecoveryManager


class TestDisasterRecovery:
    def test_backup_and_restoration_validation_drill(self):
        drm = DisasterRecoveryManager()
        backup = drm.create_backup("FULL")

        assert backup.backup_id.startswith("bk_")
        assert backup.restoration_tested is False

        # Run restoration drill
        success, msg = drm.test_restoration(backup.backup_id)
        assert success is True
        assert "passed" in msg.lower()

        status = drm.get_dr_status()
        assert status["dr_ready"] is True
        assert status["validated_restoration_backups"] == 1
