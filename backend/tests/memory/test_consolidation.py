import pytest
from app.memory.consolidation import MemoryConsolidator
from app.memory.stores.sqlite import SQLiteMemoryStore
from app.memory.models import MemoryType, VerificationStatus
from app.agent.state import AgentState, TaskState, Plan, PlanStep, StepStatus, StructuredObservation


class TestMemoryConsolidation:
    @pytest.mark.asyncio
    async def test_consolidate_completed_task(self):
        store = SQLiteMemoryStore(":memory:")
        await store.initialize()
        consolidator = MemoryConsolidator(store)

        state = AgentState(
            original_request="Inspect project and determine Python 3.12 dependencies",
            task_status=TaskState.COMPLETED,
            normalized_goal="Determine Python 3.12 dependencies",
        )
        step1 = PlanStep(id="s1", description="Search documentation", objective="Find python version", tool_name="search_web", status=StepStatus.COMPLETED)
        step2 = PlanStep(id="s2", description="Check pyproject.toml", objective="Verify dependencies", tool_name="read_file", status=StepStatus.COMPLETED)
        state.plan = Plan(plan_id="p1", goal="Check deps", steps=[step1, step2])

        state.observations.append(StructuredObservation(
            step_id="s1",
            tool_name="search_web",
            success=True,
            summary="Python 3.12 is the primary interpreter",
            evidence=[{"uri": "https://docs.python.org", "snippet": "Python 3.12 released with subinterpreters support", "authority_score": 0.95}],
        ))

        memories = await consolidator.consolidate_task(state, project_id="proj_xyz")
        assert len(memories) >= 2

        # Check types
        types = [m.memory_type for m in memories]
        assert MemoryType.TASK_HISTORY in types
        assert MemoryType.FACT in types
        assert MemoryType.PROJECT in types
        assert MemoryType.PROCEDURAL in types

        # Check provenance
        fact_mem = next(m for m in memories if m.memory_type == MemoryType.FACT)
        assert fact_mem.source == "https://docs.python.org"
        assert fact_mem.verification_status == VerificationStatus.VERIFIED
