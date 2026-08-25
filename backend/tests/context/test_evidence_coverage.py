import pytest
from app.context.planner import ContextPlanner
from app.context.evidence import EvidenceManager, EvidenceItem, EvidenceReference


class TestEvidenceCoverage:
    def test_semantic_requirement_coverage_evaluation(self):
        planner = ContextPlanner()
        em = EvidenceManager()

        plan = planner.create_context_plan("Determine whether FastAPI supports Pydantic v2 migration")

        evidence = [
            EvidenceItem(
                content="FastAPI officially supports Pydantic v2 with full compatibility and seamless migration guides.",
                reference=EvidenceReference(document_id="doc_1", chunk_id="chunk_1"),
            )
        ]

        report = em.evaluate_coverage(plan, evidence)
        assert report.total_requirements > 0
        assert report.covered_count >= 1
        assert report.coverage_score > 0.0
