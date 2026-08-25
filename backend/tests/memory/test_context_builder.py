import pytest
from app.memory.context_builder import HierarchicalContextBuilder, ContextBudget
from app.memory.models import MemoryRecord, MemoryType
from app.agent.state import AgentState, Plan, PlanStep, StepStatus, StructuredObservation


class TestContextBuilder:
    def test_build_prompt_context_with_budget(self):
        builder = HierarchicalContextBuilder(budget=ContextBudget(max_total_tokens=1000, project_memory_tokens=200))

        state = AgentState(original_request="Refactor database layer")
        state.plan = Plan(
            plan_id="p1",
            goal="Refactor DB",
            steps=[PlanStep(id="s1", description="Read models.py", objective="Inspect schema", tool_name="read_file", status=StepStatus.COMPLETED)],
        )
        state.observations.append(StructuredObservation(
            step_id="s1",
            tool_name="read_file",
            success=True,
            summary="Found 12 database models in models.py",
        ))

        proj_mem = MemoryRecord(
            content="Project uses PostgreSQL 16 with asyncpg drivers",
            memory_type=MemoryType.PROJECT,
        )

        res = builder.build_prompt_context(state, retrieved_memories=[(0.9, proj_mem)])

        assert "assembled_prompt" in res
        assert "=== CURRENT_TASK ===" in res["assembled_prompt"]
        assert "=== CURRENT_PLAN ===" in res["assembled_prompt"]
        assert "=== PROJECT_MEMORY ===" in res["assembled_prompt"]
        assert "PostgreSQL 16" in res["assembled_prompt"]
        assert res["total_tokens"] > 0
