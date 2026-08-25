import pytest
from app.platform.alerts import AlertManager, AlertSeverity


class TestAlerts:
    def test_alert_trigger_and_acknowledgment(self):
        am = AlertManager()

        alert = am.trigger_alert(
            title="Spike in Verification Failures",
            severity=AlertSeverity.HIGH,
            category="FAILURE_SPIKE",
            description="Verification failure rate reached 12%",
        )

        assert alert.alert_id.startswith("alt_")
        assert len(am.get_active_alerts(AlertSeverity.HIGH)) == 1

        # Acknowledge
        assert am.acknowledge_alert(alert.alert_id) is True
        assert len(am.get_active_alerts(AlertSeverity.HIGH)) == 0
