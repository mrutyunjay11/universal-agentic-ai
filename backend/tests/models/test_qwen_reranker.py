import pytest
from app.models.qwen_reranker import QwenRerankerProvider
from app.models.base import ModelAvailability


class TestQwenRerankerProvider:
    @pytest.mark.asyncio
    async def test_qwen_reranker_and_graceful_degradation(self):
        reranker = QwenRerankerProvider()

        query = "Python asyncio event loop exception handling"
        docs = [
            "Irrelevant recipe for apple pie baking.",
            "Handling exceptions in Python asyncio event loop tasks.",
            "Database connection pooling in PostgreSQL.",
        ]

        results = await reranker.rerank(query, docs, top_k=2)
        assert len(results) == 2
        # Highest relevance document should rank first
        assert results[0]["index"] == 1
        assert "asyncio" in results[0]["document"]

        # Test degraded fallback health status
        reranker.set_degraded(True)
        status, msg = await reranker.health_check()
        assert status == ModelAvailability.DEGRADED
        assert "RERANKER_DEGRADED" in msg
