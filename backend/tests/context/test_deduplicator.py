import pytest
from app.context.deduplicator import ContextDeduplicator
from app.context.reranker import CandidateEvidence


class TestContextDeduplicator:
    def test_deduplication_preserving_independent_corroboration(self):
        dedup = ContextDeduplicator()

        cands = [
            CandidateEvidence(
                id="doc_1",
                content="Library X version 4 deprecates legacy auth headers.",
                source_id="official_docs",
                source_type="OFFICIAL_DOCS",
            ),
            CandidateEvidence(
                id="doc_2",
                content="Library X version 4 deprecates legacy auth headers.",
                source_id="release_notes",
                source_type="RELEASE_NOTES",
            ),
            CandidateEvidence(
                id="doc_3",
                content="Library X version 4 deprecates legacy auth headers.",
                source_id="official_docs_mirror",
                source_type="OFFICIAL_DOCS",  # Exact duplicate from same source type
            ),
        ]

        unique, corroborations = dedup.deduplicate(cands)
        assert len(unique) == 1
        assert len(corroborations) == 1
        assert corroborations[0].source_type == "RELEASE_NOTES"
        assert corroborations[0].is_corroboration is True
