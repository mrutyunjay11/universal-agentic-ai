import pytest
from app.models.registry import model_registry
from app.models.router import model_router
from app.retrieval.hybrid import hybrid_retriever
from app.retrieval.candidate import RetrievalCandidate
from app.context.manager import dynamic_context_manager
from app.context.reranker import CandidateEvidence


class TestModelStackEndToEnd:
    @pytest.mark.asyncio
    async def test_complete_approved_model_architecture_workflow(self):
        # 1. Router selects Qwen3.8-Max
        reasoning_provider, model_id = await model_router.route_reasoning(task_type="RESEARCH")
        assert model_id == "Qwen3.8-Max"

        # 2. Populate Retrieval Corpus
        corpus = [
            RetrievalCandidate(
                document_id="doc_official_fastapi",
                chunk_id="chunk_1",
                source_id="fastapi_official_docs",
                source_type="OFFICIAL_DOCS",
                content="FastAPI officially supports Pydantic v2 validation models with high throughput.",
                published_year=2026,
                version="v0.110.0",
                verification_status="VERIFIED",
                authoritative_score=0.95,
            ),
            RetrievalCandidate(
                document_id="doc_legacy_blog",
                chunk_id="chunk_2",
                source_id="random_blog",
                source_type="BLOG",
                content="Older blog post about legacy setup.",
                published_year=2023,
                authoritative_score=0.3,
            ),
        ]
        hybrid_retriever.set_corpus(corpus)

        # 3. Execute Hybrid Search (Qwen3-Embedding-8B + BM25 + Qwen3-Reranker-8B)
        search_results = await hybrid_retriever.search(
            query="Verify whether FastAPI supports Pydantic v2",
            semantic_top_k=2,
            keyword_top_k=2,
            fused_top_k=2,
            reranked_top_k=2,
        )
        assert len(search_results) >= 1
        assert search_results[0].document_id == "doc_official_fastapi"

        # 4. Feed into Dynamic Context Intelligence
        candidate_evidence = [
            CandidateEvidence(
                id=c.chunk_id,
                content=c.content,
                source_id=c.document_id,
                source_type=c.source_type,
                authoritative_score=c.authoritative_score,
                published_year=c.published_year,
                version=c.version,
                verification_status=c.verification_status,
            )
            for c in search_results
        ]

        context_res = await dynamic_context_manager.build_context(
            task="Verify whether FastAPI supports Pydantic v2",
            candidates=candidate_evidence,
            constraints=["Must cite official docs"],
            model_context_limit=32768,
            task_version="v0.110.0",
        )

        assert context_res.is_sufficient is True
        assert context_res.coverage_score > 0.0
        assert "=== VERIFIED EVIDENCE ===" in context_res.active_context

        # 5. Qwen3.8-Max performs final reasoning over dynamic context
        reasoning_resp = await reasoning_provider.generate(
            prompt=context_res.active_context,
            system_prompt="You are the Universal Agentic AI reasoning core.",
        )

        assert reasoning_resp.total_tokens > 0
        assert len(reasoning_resp.content) > 0
        assert reasoning_resp.model_id == "Qwen3.8-Max"
