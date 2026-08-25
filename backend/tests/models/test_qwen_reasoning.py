import pytest
from app.models.qwen_reasoning import QwenReasoningProvider


class TestQwenReasoningProvider:
    @pytest.mark.asyncio
    async def test_qwen_generation_and_structured_output(self):
        provider = QwenReasoningProvider(model_id="Qwen3.8-Max", mode="remote")

        # 1. Plain generation
        resp = await provider.generate("Explain the dynamic context architecture")
        assert len(resp.content) > 0
        assert resp.model_id == "Qwen3.8-Max"
        assert resp.total_tokens > 0

        # 2. Structured generation
        schema = {"type": "object", "properties": {"status": {"type": "string"}}}
        struct_resp = await provider.structured_generate("Perform health analysis", schema=schema)
        assert struct_resp.structured_output is not None
        assert struct_resp.structured_output["status"] == "SUCCESS"

        # 3. Streaming
        stream_chunks = []
        async for chunk in provider.stream("Stream test prompt"):
            stream_chunks.append(chunk)
        assert len(stream_chunks) > 0
