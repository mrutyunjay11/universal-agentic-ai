from __future__ import annotations
import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.integrations.base import IntegrationStatus


class IntegrationHealthReport(BaseModel):
    connector_name: str
    provider: str
    status: IntegrationStatus
    latency_ms: int = 0
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    error_message: Optional[str] = None
    rate_limit_remaining: int = 100
    checked_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class IntegrationHealthMonitor:
    """Monitors health status and uptime metrics across all registered external system connectors."""

    def __init__(self):
        self._reports: dict[str, IntegrationHealthReport] = {}

    def record_health(
        self,
        connector_name: str,
        provider: str,
        status: IntegrationStatus,
        latency_ms: int = 0,
        error_message: Optional[str] = None,
        rate_limit_remaining: int = 100,
    ) -> IntegrationHealthReport:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        last_success = now_iso if status == IntegrationStatus.CONNECTED else None
        last_failure = now_iso if status in (IntegrationStatus.UNAVAILABLE, IntegrationStatus.AUTHENTICATION_REQUIRED) else None

        report = IntegrationHealthReport(
            connector_name=connector_name,
            provider=provider,
            status=status,
            latency_ms=latency_ms,
            last_success=last_success,
            last_failure=last_failure,
            error_message=error_message,
            rate_limit_remaining=rate_limit_remaining,
        )
        self._reports[connector_name] = report
        return report

    def get_report(self, connector_name: str) -> Optional[IntegrationHealthReport]:
        return self._reports.get(connector_name)

    def list_reports(self) -> list[IntegrationHealthReport]:
        return list(self._reports.values())


health_monitor = IntegrationHealthMonitor()
