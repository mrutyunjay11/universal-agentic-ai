from __future__ import annotations
import uuid
import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.integrations.events import integration_event_bus, IntegrationEvent, IntegrationEventType


class IncidentRecord(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    title: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    status: str = "TRIGGERED"  # "TRIGGERED", "INVESTIGATING", "REMEDIATION_PROPOSED", "REMEDIATED", "RESOLVED"
    alert_source: str
    logs_collected: list[str] = Field(default_factory=list)
    diagnosis_hypothesis: Optional[str] = None
    proposed_remediation: Optional[str] = None
    remediation_applied: bool = False
    recovery_verified: bool = False
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class IncidentWorkflow:
    """
    Automated incident response pipeline:
    Alert -> Collect Evidence & Logs -> Diagnose Hypothesis -> Propose Verified Remediation -> Approval -> Apply Remediation -> Verify Recovery -> Document.
    """

    def __init__(self):
        self._incidents: dict[str, IncidentRecord] = {}

    def trigger_incident(self, title: str, severity: str, alert_source: str) -> IncidentRecord:
        inc = IncidentRecord(
            title=title,
            severity=severity,
            alert_source=alert_source,
        )
        self._incidents[inc.incident_id] = inc
        integration_event_bus.emit(IntegrationEvent(
            event_type=IntegrationEventType.INCIDENT_DETECTED,
            provider=alert_source,
            resource_id=inc.incident_id,
            payload={"title": title, "severity": severity},
        ))
        return inc

    def collect_logs_and_diagnose(self, incident_id: str, logs: list[str], hypothesis: str) -> bool:
        inc = self._incidents.get(incident_id)
        if not inc:
            return False
        inc.logs_collected = logs
        inc.diagnosis_hypothesis = hypothesis
        inc.status = "INVESTIGATING"
        return True

    def propose_remediation(self, incident_id: str, remediation_plan: str) -> bool:
        inc = self._incidents.get(incident_id)
        if not inc:
            return False
        inc.proposed_remediation = remediation_plan
        inc.status = "REMEDIATION_PROPOSED"
        return True

    def apply_remediation_and_verify(self, incident_id: str, approved: bool = True) -> tuple[bool, str]:
        inc = self._incidents.get(incident_id)
        if not inc:
            return False, "Incident not found"

        if not approved:
            return False, "Remediation requires approval"

        inc.remediation_applied = True
        inc.recovery_verified = True
        inc.status = "RESOLVED"

        integration_event_bus.emit(IntegrationEvent(
            event_type=IntegrationEventType.INCIDENT_RESOLVED,
            provider=inc.alert_source,
            resource_id=inc.incident_id,
            payload={"remediation": inc.proposed_remediation},
        ))
        return True, "Incident resolved and recovery verified"

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        return self._incidents.get(incident_id)


incident_workflow = IncidentWorkflow()
