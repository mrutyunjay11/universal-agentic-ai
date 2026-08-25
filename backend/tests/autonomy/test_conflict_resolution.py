import pytest
from app.autonomy.conflict_resolver import ConflictResolver
from app.autonomy.policies import ConsensusStrategy


class TestConflictResolution:
    @pytest.mark.asyncio
    async def test_evidence_first_conflict_resolution(self):
        resolver = ConflictResolver()
        conflict = resolver.detect_conflict(
            task_id="task_conf_1",
            claim_a="Python 3.12 GIL is entirely removed by default",
            agent_a="Agent_A",
            confidence_a=0.90,
            evidence_a=["blog_post_unofficial"],
            claim_b="Python 3.12 maintains GIL by default, free-threading is optional via PEP 703 in 3.13",
            agent_b="Agent_B",
            confidence_b=0.88,
            evidence_b=["https://docs.python.org/3.12/whatsnew", "https://peps.python.org/pep-0703/"],
        )

        resolved = await resolver.resolve_conflict(conflict, strategy=ConsensusStrategy.EVIDENCE_FIRST)

        assert resolved.is_resolved is True
        assert resolved.winning_claim == conflict.claim_b
        assert "Agent_B" in resolved.resolution
