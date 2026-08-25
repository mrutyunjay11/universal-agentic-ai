import pytest
from app.memory.embeddings import DeterministicMockEmbedder
from app.memory.stores.vector import cosine_similarity


class TestEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_deterministic_mock_embedder(self):
        embedder = DeterministicMockEmbedder()
        v1 = await embedder.embed_text("Machine learning with neural networks")
        v2 = await embedder.embed_text("Deep learning with neural networks")
        v3 = await embedder.embed_text("Baking sourdough bread in an oven")

        assert len(v1) == 768
        assert len(v2) == 768
        assert len(v3) == 768

        sim_related = cosine_similarity(v1, v2)
        sim_unrelated = cosine_similarity(v1, v3)

        assert sim_related > sim_unrelated
        assert sim_related > 0.4
