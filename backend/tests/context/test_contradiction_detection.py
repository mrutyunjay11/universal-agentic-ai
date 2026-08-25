import pytest
from app.context.contradiction import ContradictionDetector
from app.context.evidence import EvidenceItem, EvidenceReference
from app.context.policies import ContradictionType


class TestContradictionDetection:
    def test_version_aware_and_true_contradiction_detection(self):
        detector = ContradictionDetector()

        # Version difference case
        item_v3 = EvidenceItem(
            content="Feature X is fully supported in our API.",
            reference=EvidenceReference(document_id="doc_v3", chunk_id="c1"),
            version="v3.2.0",
        )
        item_v4 = EvidenceItem(
            content="Feature X is deprecated and not supported in our API.",
            reference=EvidenceReference(document_id="doc_v4", chunk_id="c2"),
            version="v4.0.0",
        )

        rep_ver = detector.analyze_pair(item_v3, item_v4)
        assert rep_ver.has_conflict is True
        assert rep_ver.contradiction_type == ContradictionType.VERSION_DIFFERENCE

        # Genuine true contradiction (same version)
        item_same_ver_a = EvidenceItem(
            content="Feature X is fully supported in our API.",
            reference=EvidenceReference(document_id="doc_a", chunk_id="ca"),
            version="v4.0.0",
        )
        rep_true = detector.analyze_pair(item_same_ver_a, item_v4)
        assert rep_true.has_conflict is True
        assert rep_true.contradiction_type == ContradictionType.TRUE_CONTRADICTION
