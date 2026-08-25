from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class SLATarget(BaseModel):
    name: str
    target_pct: float
    current_pct: float
    status: str  # "MET", "AT_RISK", "BREACHED"


class SLAManager:
    """
    SLA / SLO compliance manager.
    Explicitly separates raw infrastructure availability from verified task correctness quality.
    """

    def __init__(self):
        self.uptime_target_pct = 99.9
        self.correctness_target_pct = 99.0
        self.latency_p95_ms_target = 5000

    def compute_slo_status(
        self,
        availability_pct: float = 99.95,
        verification_accuracy_pct: float = 99.5,
        p95_latency_ms: int = 1800,
    ) -> dict[str, Any]:
        avail_status = "MET" if availability_pct >= self.uptime_target_pct else "BREACHED"
        correct_status = "MET" if verification_accuracy_pct >= self.correctness_target_pct else "BREACHED"
        lat_status = "MET" if p95_latency_ms <= self.latency_p95_ms_target else "BREACHED"

        return {
            "overall_compliant": avail_status == "MET" and correct_status == "MET" and lat_status == "MET",
            "slos": [
                SLATarget(name="Infrastructure Availability", target_pct=self.uptime_target_pct, current_pct=availability_pct, status=avail_status).model_dump(),
                SLATarget(name="Task Correctness & Verification Quality", target_pct=self.correctness_target_pct, current_pct=verification_accuracy_pct, status=correct_status).model_dump(),
                {"name": "P95 Latency Target (ms)", "target": self.latency_p95_ms_target, "current": p95_latency_ms, "status": lat_status},
            ],
        }


sla_manager = SLAManager()
