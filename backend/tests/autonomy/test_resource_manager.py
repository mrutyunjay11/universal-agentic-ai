import pytest
from app.autonomy.resource_manager import ResourceManager


class TestResourceManager:
    def test_record_resource_usage_and_costs(self):
        rm = ResourceManager()
        rm.record_usage("t_res_1", agent_name="CoderAgent", tokens=2500, tool_calls=3, duration_ms=450)
        rm.record_usage("t_res_1", agent_name="VerifierAgent", tokens=1000, tool_calls=1, duration_ms=150)

        usage = rm.get_task_usage("t_res_1")
        assert usage.total_tokens == 3500
        assert usage.total_tool_calls == 4
        assert usage.total_execution_time_ms == 600
        assert usage.estimated_cost_usd > 0.0
        assert "CoderAgent" in usage.agent_breakdown
        assert "VerifierAgent" in usage.agent_breakdown
