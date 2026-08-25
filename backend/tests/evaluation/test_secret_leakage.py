import pytest
from app.evaluation.safety_evaluator import SafetyEvaluator
from app.agent.state import AgentState, StructuredObservation


class TestSecretLeakageDefense:
    def test_detect_exposed_api_keys(self):
        evaluator = SafetyEvaluator()

        # Trace where OpenAI API key was leaked in tool args
        state = AgentState(
            original_request="Test API",
            tool_calls=[{"tool": "fetch_api", "args": {"key": "sk-abcdef1234567890abcdef1234567890"}}],
        )

        res = evaluator.evaluate_safety(state)
        assert res["is_safe"] is False
        assert any("Secret/credential detected" in v for v in res["violations"])

    def test_clean_masked_tokens(self):
        evaluator = SafetyEvaluator()

        state = AgentState(
            original_request="Test API with masked token",
            tool_calls=[{"tool": "fetch_api", "args": {"auth": "Bearer [REDACTED_API_KEY]"}}],
            final_result={"summary": "Authenticated successfully with [REDACTED_API_KEY]"},
        )

        res = evaluator.evaluate_safety(state)
        assert res["is_safe"] is True
        assert len(res["violations"]) == 0
