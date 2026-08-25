from __future__ import annotations
import uuid
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str = Field(default_factory=lambda: f"span_{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    name: str
    service: str = "agent-platform"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: int = 0
    status: str = "OK"  # "OK", "ERROR"
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)


class DistributedTracer:
    """
    Distributed tracing subsystem.
    Generates and correlates trace IDs and span hierarchy across all microservices and async workers.
    """

    def __init__(self):
        self._spans: dict[str, list[TraceSpan]] = {}

    def start_trace(self, task_id: Optional[str] = None) -> str:
        trace_id = f"trc_{task_id or uuid.uuid4().hex[:12]}"
        self._spans[trace_id] = []
        return trace_id

    def start_span(
        self,
        trace_id: str,
        name: str,
        parent_span_id: Optional[str] = None,
        service: str = "agent-platform",
        attributes: Optional[dict[str, Any]] = None,
    ) -> TraceSpan:
        span = TraceSpan(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            service=service,
            attributes=attributes or {},
        )
        if trace_id not in self._spans:
            self._spans[trace_id] = []
        self._spans[trace_id].append(span)
        return span

    def end_span(self, span: TraceSpan, status: str = "OK", error: Optional[str] = None) -> None:
        span.end_time = time.time()
        span.duration_ms = int((span.end_time - span.start_time) * 1000)
        span.status = status
        if error:
            span.attributes["error"] = error

    def get_trace(self, trace_id: str) -> list[TraceSpan]:
        return self._spans.get(trace_id, [])

    def get_all_traces(self) -> dict[str, list[TraceSpan]]:
        return dict(self._spans)


tracer = DistributedTracer()
