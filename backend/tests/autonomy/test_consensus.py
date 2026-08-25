import pytest
from app.autonomy.consensus import ConsensusEngine
from app.autonomy.policies import ConsensusStrategy


class TestConsensusEngine:
    @pytest.mark.asyncio
    async def test_reach_consensus_with_verifier_first(self):
        engine = ConsensusEngine()
        candidates = [
            {
                "claim": "Algorithm complexity is O(N log N)",
                "agent": "ResearcherAgent",
                "confidence": 0.85,
                "evidence": ["heuristics"],
            },
            {
                "claim": "Algorithm complexity is O(N^2) due to nested loop in line 45",
                "agent": "VerifierAgent",
                "confidence": 0.98,
                "evidence": ["ast_analysis", "execution_trace"],
            },
        ]

        consensus = await engine.reach_consensus(
            task_id="task_cons_1",
            candidates=candidates,
            strategy=ConsensusStrategy.VERIFIER_FIRST,
        )

        assert consensus["consensus_reached"] is True
        assert consensus["winning_candidate"]["agent"] == "VerifierAgent"
        assert "VerifierAgent" in consensus["resolution"]
