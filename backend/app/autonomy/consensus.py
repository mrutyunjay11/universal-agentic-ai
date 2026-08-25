from __future__ import annotations
from typing import Any
from app.autonomy.policies import ConsensusStrategy
from app.autonomy.conflict_resolver import conflict_resolver, ConflictRecord


class ConsensusEngine:
    """
    Consensus engine supporting multiple evaluation and alignment strategies:
    EVIDENCE_FIRST, VERIFIER_FIRST, SOURCE_AUTHORITY, WEIGHTED_AGENT_RELIABILITY,
    MAJORITY, and HUMAN_APPROVAL.
    """

    async def reach_consensus(
        self,
        task_id: str,
        candidates: list[dict[str, Any]],
        strategy: ConsensusStrategy = ConsensusStrategy.EVIDENCE_FIRST,
    ) -> dict[str, Any]:
        if not candidates:
            return {"winning_candidate": None, "consensus_reached": False, "reason": "No candidates provided"}

        if len(candidates) == 1:
            return {"winning_candidate": candidates[0], "consensus_reached": True, "reason": "Single candidate"}

        # If two or more candidates disagree, trigger evidence-driven resolution
        cand_a = candidates[0]
        cand_b = candidates[1]

        conflict = conflict_resolver.detect_conflict(
            task_id=task_id,
            claim_a=cand_a.get("claim", str(cand_a)),
            agent_a=cand_a.get("agent", "Agent_A"),
            confidence_a=cand_a.get("confidence", 0.8),
            evidence_a=cand_a.get("evidence", []),
            claim_b=cand_b.get("claim", str(cand_b)),
            agent_b=cand_b.get("agent", "Agent_B"),
            confidence_b=cand_b.get("confidence", 0.8),
            evidence_b=cand_b.get("evidence", []),
        )

        resolved_record = await conflict_resolver.resolve_conflict(conflict, strategy=strategy)

        winning_item = cand_a if resolved_record.winning_claim == conflict.claim_a else cand_b

        return {
            "winning_candidate": winning_item,
            "consensus_reached": resolved_record.is_resolved,
            "resolution": resolved_record.resolution,
            "strategy": strategy.value,
        }


consensus_engine = ConsensusEngine()
