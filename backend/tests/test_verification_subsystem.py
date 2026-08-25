from __future__ import annotations
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.mark.asyncio
class TestVerificationSubsystem:
    async def test_extract_claims(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        sample_text = (
            "Python 3.12 was released in October 2023. "
            "The standard library math.sqrt function calculates the square root. "
            "2 + 2 equals 4. "
            "The performance improved by 15%."
        )
        res = await tool_registry.execute("extract_claims", {"text": sample_text}, ctx)
        assert res.success
        assert res.output["claim_count"] >= 3
        types = [c["claim_type"] for c in res.output["claims"]]
        assert "technical_code" in types or "mathematical" in types

    async def test_verify_calculation(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        # Correct claim
        res1 = await tool_registry.execute("verify_calculation", {"expression": "3 * 7 + 4", "claimed_result": 25.0}, ctx)
        assert res1.success
        assert res1.output["status"] == "verified"

        # False claim
        res2 = await tool_registry.execute("verify_calculation", {"expression": "10 / 2", "claimed_result": 99.0}, ctx)
        assert res2.success
        assert res2.output["status"] == "refuted"

    async def test_verify_code(self):
        ctx = ToolContext(permission_granted=PermissionTier.EXECUTE)
        valid_code = "def add(a, b): return a + b"
        res1 = await tool_registry.execute("verify_code", {"code_snippet": valid_code, "test_assertion": "assert add(2, 3) == 5"}, ctx)
        assert res1.success
        assert res1.output["status"] == "verified"

        # Code failing assertions
        res2 = await tool_registry.execute("verify_code", {"code_snippet": valid_code, "test_assertion": "assert add(2, 3) == 100"}, ctx)
        assert res2.success
        assert res2.output["status"] == "refuted"

    async def test_source_authority_and_contradiction(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        auth = await tool_registry.execute("check_source_authority", {"source_uri": "https://docs.python.org/3/library/ast.html"}, ctx)
        assert auth.success
        assert auth.output["authority_score"] >= 0.95
        assert auth.output["source_classification"] == "primary"

        contra = await tool_registry.execute("detect_contradiction", {
            "statement_a": "The function returns true on success.",
            "statement_b": "The function does not return true on success.",
        }, ctx)
        assert contra.success
        assert contra.output["contradiction_detected"] is True

    async def test_full_claim_verification_pipeline(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        evidence = [
            {"uri": "https://docs.python.org/3/library/json.html", "content": "The json module provides json.dumps and json.loads for serializing objects."},
            {"uri": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "content": "JSON.stringify and JSON.parse are built in."},
        ]
        res = await tool_registry.execute("verify_claim", {
            "claim": "Python json module provides serialization methods json.dumps and json.loads",
            "evidence_sources": evidence,
        }, ctx)
        assert res.success
        assert res.output["status"] in ("verified", "partially_verified")
        assert res.output["confidence"] >= 0.70
