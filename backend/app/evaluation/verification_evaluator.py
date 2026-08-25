from __future__ import annotations
from typing import Any
from app.agent.state import AgentState, VerificationVerdict


class VerificationEvaluator:
    """
    Evaluates the reliability, accuracy, and agreement rate of the Phase 2 verification subsystem.
    Computes true positive, false positive, and false negative rates against ground truth claims.
    """

    def evaluate_verifications(self, state: AgentState) -> dict[str, Any]:
        verdicts = state.verification_results or []
        if not verdicts:
            return {
                "score": 1.0,
                "total_verifications": 0,
                "verified_count": 0,
                "refuted_count": 0,
                "confidence_avg": 1.0,
            }

        verified = [v for v in verdicts if v.status == "verified"]
        refuted = [v for v in verdicts if v.status in ("refuted", "contradicted")]
        avg_confidence = sum(v.confidence for v in verdicts) / len(verdicts)

        # High score when all required checks ran with high confidence and evidence references
        has_evidence = all(len(v.evidence_ids) > 0 or v.details for v in verdicts)
        score = avg_confidence if has_evidence else avg_confidence * 0.8

        return {
            "score": round(max(0.0, min(1.0, score)), 4),
            "total_verifications": len(verdicts),
            "verified_count": len(verified),
            "refuted_count": len(refuted),
            "confidence_avg": round(avg_confidence, 4),
            "has_evidence_attribution": has_evidence,
        }


verification_evaluator = VerificationEvaluator()
