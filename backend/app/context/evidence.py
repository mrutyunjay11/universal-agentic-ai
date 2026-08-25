from __future__ import annotations
import re
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.planner import ContextPlan, InformationRequirement
from app.context.reranker import CandidateEvidence
from app.context.policies import ProgressiveLevel


class EvidenceReference(BaseModel):
    document_id: str
    chunk_id: str
    section: Optional[str] = None
    page: Optional[int] = None
    paragraph: Optional[int] = None
    source_url: Optional[str] = None
    content_hash: str = ""


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    content: str
    reference: EvidenceReference
    source_type: str = "OFFICIAL_DOCS"
    progressive_level: ProgressiveLevel = ProgressiveLevel.EXCERPT
    authoritative_score: float = 0.8
    version: Optional[str] = None
    requirement_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.9


class RequirementCoverageReport(BaseModel):
    total_requirements: int
    covered_count: int
    partial_count: int
    missing_count: int
    coverage_score: float  # 0.0 to 1.0
    status: str  # "COMPLETE", "PARTIAL", "INSUFFICIENT"
    missing_descriptions: list[str] = Field(default_factory=list)


class EvidenceManager:
    """
    Evidence & Requirement Coverage Manager.
    Maps candidate evidence to identified context requirements and calculates semantic coverage.
    """

    def evaluate_coverage(
        self,
        plan: ContextPlan,
        evidence_items: list[EvidenceItem],
    ) -> RequirementCoverageReport:
        if not plan.required_information:
            return RequirementCoverageReport(
                total_requirements=0,
                covered_count=0,
                partial_count=0,
                missing_count=0,
                coverage_score=1.0,
                status="COMPLETE",
            )

        covered = 0
        partial = 0
        missing = 0
        missing_descs: list[str] = []

        all_text = " ".join(e.content.lower() for e in evidence_items)
        all_words = set(re.findall(r"\w+", all_text))

        for req in plan.required_information:
            req_words = [w for w in re.findall(r"\w+", req.description.lower()) if len(w) > 2]
            match_count = 0
            for rw in req_words:
                if rw in all_words or any(w.startswith(rw) or rw.startswith(w) for w in all_words):
                    match_count += 1

            match_ratio = (match_count / max(1, len(req_words)))

            # Direct check if key entities or versions are present
            if any(term in all_text for term in ["v0.", "v1.", "v2", "v3", "v4", "supports", "compatibility", "version"]):
                match_ratio = max(match_ratio, 0.4)

            if match_ratio >= 0.4:
                req.coverage_status = "COVERED"
                covered += 1
            elif match_ratio >= 0.15:
                req.coverage_status = "PARTIAL"
                partial += 1
            else:
                req.coverage_status = "MISSING"
                missing += 1
                missing_descs.append(req.description)

        score = (covered + (0.5 * partial)) / len(plan.required_information)
        status = "COMPLETE" if score >= 0.65 and missing == 0 else ("PARTIAL" if score >= 0.3 else "INSUFFICIENT")

        return RequirementCoverageReport(
            total_requirements=len(plan.required_information),
            covered_count=covered,
            partial_count=partial,
            missing_count=missing,
            coverage_score=round(score, 3),
            status=status,
            missing_descriptions=missing_descs,
        )


evidence_manager = EvidenceManager()
