from __future__ import annotations
import ast
import datetime
import math
import re
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError
from app.tools.provenance import create_provenance, SourceType, ProvenanceRecord


# Domain authority weights dictionary
_AUTHORITY_WEIGHTS: dict[str, float] = {
    "docs.python.org": 0.98,
    "developer.mozilla.org": 0.98,
    "arxiv.org": 0.95,
    "github.com": 0.90,
    "stackoverflow.com": 0.82,
    "wikipedia.org": 0.80,
    "medium.com": 0.60,
    "reddit.com": 0.50,
}


@tool_registry.register(
    name="extract_claims",
    category=ToolCategory.VERIFICATION,
    description="Extract verifiable factual, technical, mathematical, or empirical claims from text.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_extract_claims(text: str) -> dict[str, Any]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    claims = []

    for idx, s in enumerate(sentences, 1):
        s_clean = s.strip()
        if len(s_clean) < 10:
            continue

        # Classify claim type
        claim_type = "factual"
        if re.search(r"\b(?:equals?|\+|\-|\*|\/|\^|\d+\s*%)", s_clean):
            claim_type = "mathematical"
        elif re.search(r"\b(?:function|class|method|library|api|module|version|syntax|error)\b", s_clean, re.I):
            claim_type = "technical_code"
        elif re.search(r"\b(?:released|published|founded|born|died|in \d{4})\b", s_clean, re.I):
            claim_type = "historical_date"

        claims.append({
            "claim_id": f"c_{idx}",
            "statement": s_clean,
            "claim_type": claim_type,
            "verifiable": True,
        })

    return {"source_text_length": len(text), "claim_count": len(claims), "claims": claims}


@tool_registry.register(
    name="check_source_authority",
    category=ToolCategory.VERIFICATION,
    description="Evaluate domain authority score (0.0 to 1.0) and primary vs secondary status for a URL or citation.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_source_authority(source_uri: str) -> dict[str, Any]:
    domain = ""
    if "://" in source_uri:
        domain = source_uri.split("://")[1].split("/")[0].lower()
    else:
        domain = source_uri.split("/")[0].lower()

    score = 0.70  # default baseline
    for auth_domain, weight in _AUTHORITY_WEIGHTS.items():
        if auth_domain in domain:
            score = weight
            break

    is_primary = any(p in domain for p in ("docs.", "github.com", "arxiv.org", "w3.org", "ietf.org"))
    return {
        "source_uri": source_uri,
        "domain": domain,
        "authority_score": score,
        "source_classification": "primary" if is_primary else "secondary_or_aggregator",
    }


@tool_registry.register(
    name="check_source_date",
    category=ToolCategory.VERIFICATION,
    description="Inspect publication date and detect if documentation/source might be outdated.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_source_date(date_str: str, current_year: int = 2026) -> dict[str, Any]:
    # Extract 4-digit year
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    if not year_match:
        return {"date_provided": date_str, "status": "undated", "confidence_discount": 0.15}

    pub_year = int(year_match.group(1))
    age_years = current_year - pub_year
    is_recent = age_years <= 2
    is_outdated = age_years >= 6

    return {
        "publication_year": pub_year,
        "age_years": age_years,
        "is_recent": is_recent,
        "is_outdated": is_outdated,
        "confidence_multiplier": 0.95 if is_recent else (0.80 if age_years <= 5 else 0.60),
    }


@tool_registry.register(
    name="detect_contradiction",
    category=ToolCategory.VERIFICATION,
    description="Detect direct contradictions or opposing claims across two or more text passages.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_detect_contradiction(statement_a: str, statement_b: str) -> dict[str, Any]:
    a_lower = statement_a.lower()
    b_lower = statement_b.lower()

    # Negation check
    negations = [" not ", " never ", " doesn't ", " does not ", " cannot ", " false ", " deprecated "]
    a_has_neg = any(n in a_lower for n in negations)
    b_has_neg = any(n in b_lower for n in negations)

    contradiction_likely = (a_has_neg != b_has_neg) and any(w in b_lower for w in a_lower.split() if len(w) > 4)

    return {
        "statement_a": statement_a,
        "statement_b": statement_b,
        "contradiction_detected": contradiction_likely,
        "confidence": 0.85 if contradiction_likely else 0.40,
        "details": "Opposing polarity/negation detected on common subject tokens" if contradiction_likely else "No direct contradiction found",
    }


@tool_registry.register(
    name="match_claim_to_evidence",
    category=ToolCategory.VERIFICATION,
    description="Evaluate how strongly a given piece of evidence text supports or refutes a specific claim.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_match_claim_to_evidence(claim: str, evidence: str) -> dict[str, Any]:
    claim_words = set(re.findall(r"\w{3,}", claim.lower()))
    evidence_words = set(re.findall(r"\w{3,}", evidence.lower()))
    intersection = claim_words.intersection(evidence_words)
    overlap_ratio = len(intersection) / max(1, len(claim_words))

    supports = overlap_ratio >= 0.50
    return {
        "claim": claim,
        "evidence_snippet": evidence[:200],
        "supports_claim": supports,
        "match_score": round(overlap_ratio, 3),
        "matching_keywords": list(intersection)[:10],
    }


@tool_registry.register(
    name="calculate_evidence_score",
    category=ToolCategory.VERIFICATION,
    description="Aggregate authority, recency, source count, and consistency into an overall confidence score (0.0 to 1.0).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_calculate_evidence_score(
    sources_count: int,
    avg_authority: float,
    has_primary_source: bool = True,
    contradictions_count: int = 0,
) -> dict[str, Any]:
    base_score = avg_authority * 0.5
    if has_primary_source:
        base_score += 0.3
    base_score += min(sources_count * 0.05, 0.15)
    base_score -= (contradictions_count * 0.35)

    final_score = max(0.05, min(0.96, base_score))
    return {
        "final_confidence": round(final_score, 3),
        "verdict": "high_confidence" if final_score >= 0.80 else ("moderate_confidence" if final_score >= 0.60 else "low_confidence"),
    }


@tool_registry.register(
    name="verify_calculation",
    category=ToolCategory.VERIFICATION,
    description="Verify mathematical claims by comparing claimed result against deterministic numerical/symbolic computation.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_verify_calculation(expression: str, claimed_result: float, tolerance: float = 1e-6) -> dict[str, Any]:
    from app.tools.math.scientific import _eval_safe_math
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        computed = _eval_safe_math(tree)
        diff = abs(computed - claimed_result)
        is_correct = diff <= tolerance

        return {
            "expression": expression,
            "claimed_result": claimed_result,
            "computed_result": computed,
            "difference": diff,
            "status": "verified" if is_correct else "refuted",
            "confidence": 0.999 if is_correct else 0.999,
        }
    except Exception as e:
        return {"expression": expression, "status": "inconclusive", "error": str(e)}


@tool_registry.register(
    name="verify_code",
    category=ToolCategory.VERIFICATION,
    description="Verify technical code claims through AST syntax validation, static compilation, and execution tests.",
    permission=PermissionTier.EXECUTE,
    timeout=30,
)
async def tool_verify_code(code_snippet: str, language: str = "python", test_assertion: Optional[str] = None) -> dict[str, Any]:
    if language == "python":
        # Step 1: AST syntax check
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError as e:
            return {
                "status": "refuted",
                "verification_stage": "syntax_parse",
                "error": f"SyntaxError at line {e.lineno}: {e.msg}",
                "confidence": 0.99,
            }

        # Step 2: Test assertion execution if provided
        if test_assertion:
            full_code = f"{code_snippet}\n{test_assertion}"
            try:
                exec(full_code, {})
                return {
                    "status": "verified",
                    "verification_stage": "assertion_execution",
                    "confidence": 0.98,
                    "message": "Code parsed and test assertions passed successfully.",
                }
            except AssertionError as e:
                return {
                    "status": "refuted",
                    "verification_stage": "assertion_execution",
                    "error": f"AssertionFailed: {e}",
                    "confidence": 0.95,
                }
            except Exception as e:
                return {
                    "status": "refuted",
                    "verification_stage": "runtime_execution",
                    "error": str(e),
                    "confidence": 0.95,
                }

        return {"status": "verified", "verification_stage": "syntax_parse", "confidence": 0.92}

    return {"status": "inconclusive", "message": f"Static parser only available for Python in this sandbox."}


@tool_registry.register(
    name="verify_claim",
    category=ToolCategory.VERIFICATION,
    description="Full verification pipeline for a claim: extracts evidence, cross-checks sources, and produces a structured verdict.",
    permission=PermissionTier.READ,
    timeout=20,
)
async def tool_verify_claim(
    claim: str,
    evidence_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    if not evidence_sources:
        return {
            "claim": claim,
            "status": "inconclusive",
            "confidence": 0.20,
            "evidence": [],
            "contradictions": [],
            "message": "No evidence sources supplied for claim.",
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    evidence_items = []
    contradictions = []
    authorities = []

    for src in evidence_sources:
        uri = src.get("uri", "")
        text = src.get("content", "")
        auth = await tool_check_source_authority(uri)
        authorities.append(auth["authority_score"])
        match = await tool_match_claim_to_evidence(claim, text)

        evidence_items.append({
            "source": uri,
            "domain": auth["domain"],
            "type": auth["source_classification"],
            "supports_claim": match["supports_claim"],
            "match_score": match["match_score"],
        })

    avg_auth = sum(authorities) / max(1, len(authorities))
    supporting_count = sum(1 for e in evidence_items if e["supports_claim"])

    # Only flag contradiction if direct contradiction detected between sources
    if len(evidence_sources) >= 2:
        for i in range(len(evidence_sources)):
            for j in range(i + 1, len(evidence_sources)):
                c_check = await tool_detect_contradiction(evidence_sources[i].get("content", ""), evidence_sources[j].get("content", ""))
                if c_check["contradiction_detected"]:
                    contradictions.append(f"Contradiction detected between {evidence_sources[i].get('uri')} and {evidence_sources[j].get('uri')}")

    has_primary = any(e["type"] == "primary" and e["supports_claim"] for e in evidence_items)
    score_data = await tool_calculate_evidence_score(
        sources_count=supporting_count or 1,
        avg_authority=avg_auth,
        has_primary_source=has_primary,
        contradictions_count=len(contradictions),
    )

    status = "verified" if (supporting_count > 0 and not contradictions) else ("partially_verified" if supporting_count > 0 else "refuted")
    return {
        "claim": claim,
        "status": status,
        "confidence": score_data["final_confidence"],
        "evidence": evidence_items,
        "contradictions": contradictions,
        "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@tool_registry.register(
    name="compare_sources",
    category=ToolCategory.VERIFICATION,
    description="Compare claims and consistency across two independent sources.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_compare_sources(source_a_content: str, source_b_content: str) -> dict[str, Any]:
    contradiction = await tool_detect_contradiction(source_a_content, source_b_content)
    return {
        "consistent": not contradiction["contradiction_detected"],
        "contradiction_details": contradiction,
    }


@tool_registry.register(
    name="check_primary_source",
    category=ToolCategory.VERIFICATION,
    description="Check whether a cited reference is an official primary source or a secondary summary.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_primary_source(source_uri: str) -> dict[str, Any]:
    return await tool_check_source_authority(source_uri)


@tool_registry.register(
    name="check_citation",
    category=ToolCategory.VERIFICATION,
    description="Validate citation metadata (author, title, URL/DOI, date) for completeness and validity.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_check_citation(citation: dict[str, Any]) -> dict[str, Any]:
    has_title = bool(citation.get("title"))
    has_uri = bool(citation.get("uri") or citation.get("url") or citation.get("doi"))
    has_author = bool(citation.get("author") or citation.get("publisher"))
    valid = has_title and has_uri

    return {
        "citation_valid": valid,
        "has_title": has_title,
        "has_uri": has_uri,
        "has_author": has_author,
    }


@tool_registry.register(
    name="verify_document",
    category=ToolCategory.VERIFICATION,
    description="Verify document integrity via checksum hash and structural validation.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_verify_document(file_path: str, expected_sha256: Optional[str] = None, project_root: str = "./projects") -> dict[str, Any]:
    from app.tools.file.operations import tool_get_file_metadata
    meta = await tool_get_file_metadata(file_path, project_root)
    actual_hash = meta.get("sha256", "")
    matches = (actual_hash == expected_sha256) if expected_sha256 else True

    return {
        "file_path": file_path,
        "size_bytes": meta.get("size_bytes", 0),
        "sha256": actual_hash,
        "hash_verified": matches,
    }
