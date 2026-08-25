import pytest
from app.context.reranker import EvidenceReranker, CandidateEvidence


class TestDistractorRobustness:
    def test_ranking_resistance_to_noisy_distractors(self):
        reranker = EvidenceReranker()

        relevant = CandidateEvidence(
            id="doc_rel",
            content="FastAPI authentication uses OAuth2 with PasswordBearer tokens.",
            source_id="official_docs",
            source_type="OFFICIAL_DOCS",
            authoritative_score=0.95,
            semantic_similarity=0.90,
        )

        distractors = [
            CandidateEvidence(
                id=f"doc_distractor_{i}",
                content=f"Irrelevant content about unrelated topic {i} without authentication details.",
                source_id=f"distractor_{i}",
                source_type="BLOG",
                authoritative_score=0.2,
                semantic_similarity=0.3,
            )
            for i in range(10)
        ]

        all_cands = distractors + [relevant]
        ranked = reranker.rerank("FastAPI authentication OAuth2", all_cands, top_k=3)

        assert ranked[0].id == "doc_rel"
        assert ranked[0].composite_score > ranked[1].composite_score
