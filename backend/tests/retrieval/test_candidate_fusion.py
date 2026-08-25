import pytest
from app.retrieval.hybrid import HybridRetriever, FusionStrategy
from app.retrieval.candidate import RetrievalCandidate


class TestCandidateFusion:
    @pytest.mark.asyncio
    async def test_reciprocal_rank_fusion_and_weighted_fusion(self):
        retriever = HybridRetriever()

        corpus = [
            RetrievalCandidate(
                document_id="doc_fastapi",
                chunk_id="c1",
                source_id="official_docs",
                content="FastAPI officially supports Pydantic v2 validation models.",
            ),
            RetrievalCandidate(
                document_id="doc_unrelated",
                chunk_id="c2",
                source_id="blog",
                content="Unrelated tutorial about web design and CSS colors.",
            ),
        ]

        retriever.set_corpus(corpus)

        # 1. Test RRF
        results_rrf = await retriever.search(
            query="FastAPI Pydantic v2",
            fusion_strategy=FusionStrategy.RRF,
            fused_top_k=2,
            reranked_top_k=2,
        )
        assert len(results_rrf) >= 1
        assert results_rrf[0].document_id == "doc_fastapi"

        # 2. Test Weighted Fusion
        results_weighted = await retriever.search(
            query="FastAPI Pydantic v2",
            fusion_strategy=FusionStrategy.WEIGHTED,
            fused_top_k=2,
            reranked_top_k=2,
        )
        assert len(results_weighted) >= 1
        assert results_weighted[0].document_id == "doc_fastapi"
