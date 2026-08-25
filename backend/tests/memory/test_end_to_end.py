import pytest
from app.memory.manager import MemoryManager
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus
from app.agent.agent import universal_agent
from app.tools.permissions import PermissionTier


class TestMemoryEndToEndScenarios:
    @pytest.mark.asyncio
    async def test_scenario_a_conversation_continuity(self):
        # Scenario A: Conversation continuity & preference recall across tasks
        manager = MemoryManager()
        await manager.initialize()

        # Session 1: User establishes preference
        await manager.remember(
            content="User prefers strict type hinting and dataclasses for Python models",
            memory_type=MemoryType.USER_PREFERENCE,
            scope=MemoryScope.USER,
            user_id="dev_user_1",
            confidence=0.95,
            importance=0.9,
            verification_status=VerificationStatus.SUPPORTED,
        )

        # Session 2: Later task retrieves the preference
        recalled = await manager.retrieve(
            query="coding style and model architecture preference",
            user_id="dev_user_1",
        )
        assert len(recalled) >= 1
        assert "strict type hinting and dataclasses" in recalled[0][1].content
        assert recalled[0][1].access_count >= 1

    @pytest.mark.asyncio
    async def test_scenario_b_project_memory_persistence(self):
        # Scenario B: Agent discovers project fact -> Later task retrieves that fact
        manager = MemoryManager()
        await manager.initialize()

        # Task 1: Discovers project uses pytest with asyncio strict mode
        await manager.remember(
            content="Project uses pytest with asyncio_mode = strict in pytest.ini",
            memory_type=MemoryType.PROJECT,
            scope=MemoryScope.PROJECT,
            project_id="backend_repo",
            confidence=1.0,
            importance=0.9,
            verification_status=VerificationStatus.VERIFIED,
            tags=["pytest", "asyncio", "config"],
        )

        # Task 2: Later task in backend_repo retrieves the config
        retrieved = await manager.retrieve(
            query="How are tests configured in this repo?",
            project_id="backend_repo",
        )
        assert len(retrieved) >= 1
        assert "asyncio_mode = strict" in retrieved[0][1].content

    @pytest.mark.asyncio
    async def test_scenario_c_stale_information_detection(self):
        # Scenario C: Dependency updates -> Old memory marked stale
        manager = MemoryManager()
        await manager.initialize()

        rec = await manager.remember(
            content="Project uses Node 16 with Webpack 4",
            memory_type=MemoryType.PROJECT,
            project_id="webapp_repo",
            confidence=0.8,
        )

        # Update detected: Mark old memory STALE / EXPIRED
        audit = await manager.invalidate(
            memory_id=rec.id,
            reason="Project upgraded to Node 20 with Vite",
            new_status=FreshnessStatus.STALE,
        )
        assert audit is not None
        assert audit.new_status == FreshnessStatus.STALE

        # Retrieving without include_stale should ignore it
        active_results = await manager.retrieve(
            query="Node and bundler setup",
            project_id="webapp_repo",
            include_stale=False,
        )
        assert not any(r[1].id == rec.id for r in active_results)

    @pytest.mark.asyncio
    async def test_scenario_d_contradiction_superseding(self):
        # Scenario D: Old memory: Feature exists -> New official documentation: Feature removed
        manager = MemoryManager()
        await manager.initialize()

        old_mem = await manager.remember(
            content="Python 3.11 supports legacy asyncio.coroutine decorator",
            memory_type=MemoryType.FACT,
            confidence=0.9,
            verification_status=VerificationStatus.VERIFIED,
        )

        new_mem = MemoryRecord(
            content="Python 3.12 completely removed asyncio.coroutine decorator; use async def",
            memory_type=MemoryType.FACT,
            confidence=0.99,
            verification_status=VerificationStatus.VERIFIED,
            source="https://docs.python.org/3.12/whatsnew/3.12.html",
        )

        # Supersede old memory with new verified knowledge
        audit = await manager.supersede(
            old_memory_id=old_mem.id,
            new_memory=new_mem,
            reason="asyncio.coroutine removed in 3.12 release",
        )
        assert audit is not None
        assert audit.previous_status == FreshnessStatus.CURRENT
        assert audit.new_status == FreshnessStatus.SUPERSEDED

        # Retrieval should return the new current memory over the superseded memory
        res = await manager.retrieve(query="asyncio.coroutine decorator support in Python")
        assert len(res) >= 1
        assert "completely removed" in res[0][1].content

    @pytest.mark.asyncio
    async def test_scenario_e_large_context_compression_and_traceability(self):
        # Scenario E: Large context + evidence preservation
        manager = MemoryManager()
        await manager.initialize()

        state = universal_agent.create_task(
            request="Analyze voluminous logs and extract critical root cause",
            permission_granted=PermissionTier.SYSTEM,
        )
        state.evidence.append({
            "uri": "https://logs.internal.service/error_trace_4048",
            "snippet": "CRITICAL: Database connection pool exhausted at max_connections=100",
            "authority_score": 0.99,
        })

        mem = MemoryRecord(
            content="Database connection pool configuration limit is 100",
            memory_type=MemoryType.FACT,
            source="https://logs.internal.service/error_trace_4048",
        )

        ctx = manager.build_context(state, retrieved_memories=[(0.95, mem)])
        assert "=== EVIDENCE ===" in ctx["assembled_prompt"]
        assert "Database connection pool exhausted" in ctx["assembled_prompt"]
        assert "EVIDENCE" in ctx["provenance_map"]
        assert "https://logs.internal.service/error_trace_4048" in ctx["provenance_map"]["EVIDENCE"]
