import pytest
from app.platform.tracing import DistributedTracer


class TestDistributedTracing:
    def test_trace_and_span_hierarchy(self):
        dt = DistributedTracer()
        trace_id = dt.start_trace("task_root_99")

        # Root span: Orchestrator
        root_span = dt.start_span(trace_id, name="Orchestrator.Execute")

        # Child span: Tool
        child_span = dt.start_span(
            trace_id,
            name="Tool.Execute",
            parent_span_id=root_span.span_id,
            attributes={"tool_name": "calculator"},
        )

        dt.end_span(child_span, status="OK")
        dt.end_span(root_span, status="OK")

        spans = dt.get_trace(trace_id)
        assert len(spans) == 2
        assert spans[1].parent_span_id == spans[0].span_id
