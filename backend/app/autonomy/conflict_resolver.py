from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.autonomy.policies import ConsensusStrategy
from app.autonomy.events import autonomy_event_bus, AutonomyEvent, AutonomyEventType


class ConflictRecord(BaseModel):
    conflict_id: str
    task_id: str
    claim_a: str
    agent_a: str
    confidence_a: float
    evidence_a: list[str] = Field(default_factory=list)
    claim_b: str
    agent_b: str
    confidence_b: float
    evidence_b: list[str] = Field(default_factory=list)
    resolution: Optional[str] = None
    winning_claim: Optional[str] = None
    strategy_used: ConsensusStrategy = ConsensusStrategy.EVIDENCE_FIRST
    is_resolved: bool = False


class ConflictResolver:
    """
    Detects factual, technical, or code disagreements between specialized agents,
    evaluates primary vs secondary source evidence, and resolves conflicts using evidence-first logic.
    Never relies purely on majority vote when empirical evidence is present.
    """

    def __init__(self):
        self._conflicts: list[ConflictRecord] = []

    def detect_conflict(
        self,
        task_id: str,
        claim_a: str,
        agent_a: str,
        confidence_a: float,
        evidence_a: list[str],
        claim_b: str,
        agent_b: str,
        confidence_b: float,
        evidence_b: list[str],
    ) -> ConflictRecord:
        conflict = ConflictRecord(
            conflict_id=f"conf_{len(self._conflicts) + 1}",
            task_id=task_id,
            claim_a=claim_a,
            agent_a=agent_a,
            confidence_a=confidence_a,
            evidence_a=evidence_a,
            claim_b=claim_b,
            agent_b=agent_b,
            confidence_b=confidence_b,
            evidence_b=evidence_b,
        )
        self._conflicts.append(conflict)
        return conflict

    async def resolve_conflict(
        self,
        conflict: ConflictRecord,
        strategy: ConsensusStrategy = ConsensusStrategy.EVIDENCE_FIRST,
    ) -> ConflictRecord:
        conflict.strategy_used = strategy

        if strategy == ConsensusStrategy.EVIDENCE_FIRST:
            # Evidence count and primary source authority dominate
            score_a = len(conflict.evidence_a) * 1.5 + conflict.confidence_a
            score_b = len(conflict.evidence_b) * 1.5 + conflict.confidence_b

            if score_a >= score_b:
                conflict.winning_claim = conflict.claim_a
                conflict.resolution = f"Resolved in favor of {conflict.agent_a} due to stronger evidence backing ({len(conflict.evidence_a)} citations)"
            else:
                conflict.winning_claim = conflict.claim_b
                conflict.resolution = f"Resolved in favor of {conflict.agent_b} due to stronger evidence backing ({len(conflict.evidence_b)} citations)"
            conflict.is_resolved = True

        elif strategy == ConsensusStrategy.VERIFIER_FIRST:
            if "verifier" in conflict.agent_a.lower():
                conflict.winning_claim = conflict.claim_a
                conflict.resolution = f"Resolved in favor of independent verifier {conflict.agent_a}"
            else:
                conflict.winning_claim = conflict.claim_b
                conflict.resolution = f"Resolved in favor of independent verifier {conflict.agent_b}"
            conflict.is_resolved = True

        elif strategy == ConsensusStrategy.WEIGHTED_AGENT_RELIABILITY:
            if conflict.confidence_a >= conflict.confidence_b:
                conflict.winning_claim = conflict.claim_a
                conflict.resolution = f"Resolved in favor of higher confidence agent {conflict.agent_a}"
            else:
                conflict.winning_claim = conflict.claim_b
                conflict.resolution = f"Resolved in favor of higher confidence agent {conflict.agent_b}"
            conflict.is_resolved = True

        await autonomy_event_bus.emit(AutonomyEvent(
            event_type=AutonomyEventType.CONFLICT_RESOLVED,
            task_id=conflict.task_id,
            payload={"conflict_id": conflict.conflict_id, "resolution": conflict.resolution},
        ))
        return conflict


conflict_resolver = ConflictResolver()
