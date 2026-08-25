from __future__ import annotations
import uuid
import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PlatformAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: f"alt_{uuid.uuid4().hex[:8]}")
    title: str
    severity: AlertSeverity
    category: str  # "FAILURE_SPIKE", "SECURITY_VIOLATION", "LATENCY_SPIKE", "BUDGET_OVERRUN"
    description: str
    source_service: str
    acknowledged: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class AlertManager:
    """
    Real-time platform alert manager.
    Detects failure rate spikes, security policy violations, permission bypasses,
    unusual latency degradation, and cost overruns.
    """

    def __init__(self):
        self._alerts: list[PlatformAlert] = []

    def trigger_alert(
        self,
        title: str,
        severity: AlertSeverity,
        category: str,
        description: str,
        source_service: str = "agent-platform",
    ) -> PlatformAlert:
        alert = PlatformAlert(
            title=title,
            severity=severity,
            category=category,
            description=description,
            source_service=source_service,
        )
        self._alerts.append(alert)
        return alert

    def acknowledge_alert(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return True
        return False

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> list[PlatformAlert]:
        return [
            a for a in self._alerts
            if not a.acknowledged and (severity is None or a.severity == severity)
        ]

    def list_all_alerts(self) -> list[PlatformAlert]:
        return list(self._alerts)


alert_manager = AlertManager()
