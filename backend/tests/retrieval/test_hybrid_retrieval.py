import pytest
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.candidate import RetrievalCandidate


class TestHybridRetrieval:
    @pytest.mark.asyncio
    async def test_two_stage_hybrid_retrieval_and_reranking(self):
        retriever = HybridRetriever()

        corpus = [
            RetrievalCandidate(
                document_id="doc_auth",
                chunk_id="c1",
                source_id="sec_docs",
                content="Authentication with OAuth2 Bearer Tokens and JWT verification in Python.",
            ),
            RetrievalCandidate(
                document_id="doc_perf",
                chunk_id="c2",
                source_id="perf_docs",
                content="Performance benchmarking and latency optimization in web servers.",
            ),
            RetrievalCandidate(
                document_id="doc_misc",
                chunk_id="c3",
                source_id="misc_docs",
                content="Miscellaneous helper utilities and string formatting functions.",
            ),
        ]

        retriever.set_corpus(corpus)

        results = await retriever.search(
            query="OAuth2 JWT authentication tokens",
            semantic_top_k=2,
            keyword_top_k=2,
            fused_top_k=2,
            reranked_top_k=1,
        )

        assert len(results) == 1
        assert results[0].document_id == "doc_auth"
        assert results[0].reranker_score > 0.0
