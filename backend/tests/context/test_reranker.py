import pytest
from app.context.reranker import EvidenceReranker, CandidateEvidence


class TestEvidenceReranker:
    def test_multi_factor_reranking_and_authority_weighting(self):
        reranker = EvidenceReranker()

        cands = [
            CandidateEvidence(
                id="doc_blog",
                content="FastAPI is a great framework with async support",
                source_id="blog_post_1",
                source_type="BLOG",
                authoritative_score=0.4,
                semantic_similarity=0.8,
            ),
            CandidateEvidence(
                id="doc_official",
                content="FastAPI officially supports Pydantic v2 fully with BaseModel validation",
                source_id="official_docs",
                source_type="OFFICIAL_DOCS",
                authoritative_score=0.95,
                semantic_similarity=0.85,
                verification_status="VERIFIED",
            ),
        ]

        ranked = reranker.rerank("FastAPI Pydantic v2 support", cands)
        assert len(ranked) == 2
        # Official verified docs must rank first due to authority and verification weights
        assert ranked[0].id == "doc_official"
        assert ranked[0].composite_score > ranked[1].composite_score
