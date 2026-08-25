import pytest
from app.context.manager import DynamicContextManager
from app.context.reranker import CandidateEvidence


class TestDynamicContextEndToEnd:
    @pytest.mark.asyncio
    async def test_complete_dynamic_context_lifecycle(self):
        dcm = DynamicContextManager()

        candidates = [
            CandidateEvidence(
                id="doc_fastapi_docs",
                content="FastAPI officially supports Pydantic v2 validation models with high throughput.",
                source_id="fastapi_docs_main",
                source_type="OFFICIAL_DOCS",
                authoritative_score=0.95,
                published_year=2026,
                verification_status="VERIFIED",
                version="v0.110.0",
            ),
            CandidateEvidence(
                id="doc_blog_unverified",
                content="Some unverified blog post claiming generic setup instructions.",
                source_id="blog_random",
                source_type="BLOG",
                authoritative_score=0.3,
                published_year=2024,
            ),
            CandidateEvidence(
                id="doc_release_notes",
                content="FastAPI officially supports Pydantic v2 validation models with high throughput.",
                source_id="fastapi_releases",
                source_type="RELEASE_NOTES",
                authoritative_score=0.9,
                published_year=2026,
                version="v0.110.0",
            ),
        ]

        result = await dcm.build_context(
            task="Verify whether FastAPI supports Pydantic v2",
            candidates=candidates,
            constraints=["Must cite official docs"],
            model_context_limit=16384,
            task_version="v0.110.0",
        )

        assert result.plan_id.startswith("cplan_")
        assert result.coverage_score > 0.0
        assert result.is_sufficient is True
        assert "=== VERIFIED EVIDENCE ===" in result.active_context
        assert "<EXTERNAL_DATA" in result.active_context
        assert "FastAPI officially supports Pydantic v2" in result.active_context
        assert result.selected_evidence_count >= 1
        assert result.total_tokens > 0
