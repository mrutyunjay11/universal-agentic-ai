import pytest
from app.evaluation.factuality import FactualityEvaluator, FactualityVerdict
from app.agent.state import AgentState, StructuredObservation, VerificationVerdict


class TestFactualityEvaluator:
    def test_factuality_supported_by_evidence(self):
        evaluator = FactualityEvaluator()
        state = AgentState(
            original_request="Verify python asyncio features",
            final_result={"summary": "Python 3.12 supports subinterpreters according to official docs."},
        )
        state.evidence.append({
            "uri": "https://docs.python.org/3.12",
            "snippet": "Python 3.12 supports subinterpreters via PEP 684",
        })
        state.verification_results.append(VerificationVerdict(
            step_id="s1",
            claim="Python 3.12 supports subinterpreters",
            status="verified",
            confidence=0.95,
            evidence_ids=["https://docs.python.org/3.12"],
            details={},
        ))

        res = evaluator.evaluate_factuality(state)
        assert res["factuality_score"] >= 0.85
        assert res["claims_evaluated"] >= 1
        assert res["has_contradictions"] is False

    def test_factuality_contradiction_penalty(self):
        evaluator = FactualityEvaluator()
        state = AgentState(
            original_request="Check math claim",
            final_result={"summary": "Claimed result is 500"},
        )
        state.verification_results.append(VerificationVerdict(
            step_id="s1",
            claim="Claimed result is 500",
            status="refuted",
            confidence=0.99,
            evidence_ids=[],
            details={"computed_result": 200},
        ))

        res = evaluator.evaluate_factuality(state)
        assert res["has_contradictions"] is True
        assert res["factuality_score"] < 0.80
