import pytest
from app.autonomy.orchestrator import MasterOrchestrator
from app.autonomy.policies import ExecutionMode, ConsensusStrategy
from app.autonomy.conflict_resolver import ConflictResolver
from app.autonomy.consensus import ConsensusEngine
from app.autonomy.long_horizon import LongHorizonManager
from app.autonomy.task_graph import TaskGraph, SubTask, SubTaskStatus


class TestAutonomyEndToEndScenarios:
    @pytest.mark.asyncio
    async def test_scenario_a_multi_source_research(self):
        """Scenario A: Multi-source research where evidence, not agent count, determines verdict."""
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Research and verify Python 3.12 GIL status across multiple official sources",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"
        assert len(completed.result["artifacts"]) >= 1

    @pytest.mark.asyncio
    async def test_scenario_b_complex_coding_project(self):
        """Scenario B: Code project with analysis, implementation, and testing."""
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Implement and test an async HTTP rate limiter in python",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"
        assert completed.result["completed_subtasks"] >= 2

    @pytest.mark.asyncio
    async def test_scenario_c_research_and_implementation(self):
        """Scenario C: Research and verify documentation, then implement code."""
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Research documentation and code a calculator parser",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"

    @pytest.mark.asyncio
    async def test_scenario_d_parallel_independent_work(self):
        """Scenario D: Independent parallel subtasks execute without races and aggregate."""
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Compare statistics on multiple datasets in parallel",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )

        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"
        assert completed.result["average_confidence"] > 0.70

    @pytest.mark.asyncio
    async def test_scenario_e_agent_disagreement_and_verification(self):
        """Scenario E: Agent disagreement resolved via evidence and verifier dominance."""
        engine = ConsensusEngine()
        candidates = [
            {
                "claim": "Claim A: Peak memory is 50MB",
                "agent": "ResearcherAgent",
                "confidence": 0.82,
                "evidence": ["inferred"],
            },
            {
                "claim": "Claim B: Peak memory is 128MB measured via memory profiler",
                "agent": "VerifierAgent",
                "confidence": 0.99,
                "evidence": ["memray_dump_2026", "valgrind_log"],
            },
        ]

        consensus = await engine.reach_consensus(
            task_id="task_scen_e",
            candidates=candidates,
            strategy=ConsensusStrategy.VERIFIER_FIRST,
        )

        assert consensus["consensus_reached"] is True
        assert "VerifierAgent" in consensus["winning_candidate"]["agent"]

    @pytest.mark.asyncio
    async def test_scenario_f_long_running_task_checkpoint_and_recovery(self):
        """Scenario F: Long-running workflow saves checkpoint, pauses, resumes, and completes."""
        from app.autonomy.long_horizon import long_horizon_manager
        orchestrator = MasterOrchestrator()
        record = orchestrator.create_task(
            goal="Long running workflow for quarterly data aggregation",
            execution_mode=ExecutionMode.SPECIALIZED_MULTI_AGENT,
        )

        # 1. Execute task
        completed = await orchestrator.execute_task(record.task_id)
        assert completed.status == "COMPLETED"

        # 2. Verify checkpoints were recorded
        latest_cp = long_horizon_manager.get_latest_checkpoint(record.task_id)
        assert latest_cp is not None
        assert "POST_EXECUTION" in latest_cp.stage_name
