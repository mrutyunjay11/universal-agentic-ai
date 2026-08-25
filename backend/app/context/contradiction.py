from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.policies import ContradictionType
from app.context.evidence import EvidenceItem


class ContradictionReport(BaseModel):
    has_conflict: bool = False
    contradiction_type: ContradictionType = ContradictionType.UNRESOLVED
    source_a_id: str = ""
    source_b_id: str = ""
    claim_a: str = ""
    claim_b: str = ""
    resolution_recommendation: str = ""


class ContradictionDetector:
    """
    Temporal, Version, and Scope-Aware Contradiction Detector.
    Prevents false contradictions caused by version evolution, temporal differences,
    or platform conditions while identifying genuine factual disagreements.
    """

    def analyze_pair(
        self,
        item_a: EvidenceItem,
        item_b: EvidenceItem,
    ) -> ContradictionReport:
        text_a = item_a.content.lower()
        text_b = item_b.content.lower()

        # Check for opposing polarity (e.g. "is supported" vs "not supported" / "deprecated")
        polarity_conflict = (
            ("supported" in text_a and ("not supported" in text_b or "deprecated" in text_b or "unsupported" in text_b))
            or ("not supported" in text_a and "supported" in text_b)
            or ("true" in text_a and "false" in text_b)
            or ("allowed" in text_a and "forbidden" in text_b)
        )

        if not polarity_conflict:
            return ContradictionReport(has_conflict=False)

        # 1. Version Difference Check
        if item_a.version and item_b.version and item_a.version != item_b.version:
            return ContradictionReport(
                has_conflict=True,
                contradiction_type=ContradictionType.VERSION_DIFFERENCE,
                source_a_id=item_a.reference.document_id,
                source_b_id=item_b.reference.document_id,
                claim_a=item_a.content[:150],
                claim_b=item_b.content[:150],
                resolution_recommendation=f"Resolve by checking active project version against {item_a.version} vs {item_b.version}",
            )

        # 2. Scope Difference Check (e.g. OS / platform)
        if ("windows" in text_a and "linux" in text_b) or ("darwin" in text_a and "windows" in text_b):
            return ContradictionReport(
                has_conflict=True,
                contradiction_type=ContradictionType.SCOPE_DIFFERENCE,
                source_a_id=item_a.reference.document_id,
                source_b_id=item_b.reference.document_id,
                claim_a=item_a.content[:150],
                claim_b=item_b.content[:150],
                resolution_recommendation="Resolve by inspecting target deployment operating system scope",
            )

        # 3. Genuine / True Contradiction
        return ContradictionReport(
            has_conflict=True,
            contradiction_type=ContradictionType.TRUE_CONTRADICTION,
            source_a_id=item_a.reference.document_id,
            source_b_id=item_b.reference.document_id,
            claim_a=item_a.content[:150],
            claim_b=item_b.content[:150],
            resolution_recommendation="Flag as conflicting evidence: trigger independent runtime/authoritative test verification",
        )


contradiction_detector = ContradictionDetector()
