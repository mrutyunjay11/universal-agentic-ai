import pytest
from app.models.qwen_embedding import QwenEmbeddingProvider, VectorIndexMetadata


class TestQwenEmbeddingProvider:
    @pytest.mark.asyncio
    async def test_qwen_embedding_and_index_compatibility(self):
        provider = QwenEmbeddingProvider(dimension=4096)

        query_vec = await provider.embed_query("FastAPI Pydantic v2 migration")
        assert len(query_vec) == 4096
        assert all(isinstance(v, float) for v in query_vec)

        doc_vecs = await provider.embed_documents([
            "Official documentation for FastAPI",
            "Pydantic v2 compatibility matrix",
        ])
        assert len(doc_vecs) == 2
        assert len(doc_vecs[0]) == 4096

        # Index metadata compatibility validation
        valid_meta = VectorIndexMetadata(
            embedding_model="Qwen/Qwen3-Embedding-8B",
            dimension=4096,
        )
        is_compat, _ = provider.validate_index_compatibility(valid_meta)
        assert is_compat is True

        incompat_meta = VectorIndexMetadata(
            embedding_model="Legacy-Embed-Model",
            dimension=768,
        )
        is_incompat, err_msg = provider.validate_index_compatibility(incompat_meta)
        assert is_incompat is False
        assert "Incompatible embedding model" in err_msg
