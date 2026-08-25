import pytest
from app.models.registry import ModelRegistry
from app.models.base import ModelRole, ModelAvailability


class TestModelRegistry:
    @pytest.mark.asyncio
    async def test_registry_registration_and_health_checks(self):
        reg = ModelRegistry()

        # Check default registrations
        qwen_reasoning = reg.get_reasoning_provider("Qwen3.8-Max")
        assert qwen_reasoning is not None
        assert qwen_reasoning.metadata.role == ModelRole.REASONING

        qwen_embed = reg.get_embedding_provider("Qwen/Qwen3-Embedding-8B")
        assert qwen_embed is not None
        assert qwen_embed.metadata.role == ModelRole.EMBEDDING

        qwen_rerank = reg.get_reranker_provider("Qwen/Qwen3-Reranker-8B")
        assert qwen_rerank is not None
        assert qwen_rerank.metadata.role == ModelRole.RERANKER

        # Run health checks
        report = await reg.run_health_checks()
        assert "Qwen3.8-Max" in report
        assert report["Qwen3.8-Max"]["status"] == ModelAvailability.READY.value
        assert "Qwen/Qwen3-Embedding-8B" in report
        assert "Qwen/Qwen3-Reranker-8B" in report
