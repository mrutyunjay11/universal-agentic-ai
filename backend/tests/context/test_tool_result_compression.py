import pytest
from app.context.compressor import SemanticCompressor
from app.context.evidence import EvidenceItem, EvidenceReference


class TestToolResultCompression:
    def test_large_tool_result_externalization_and_compression(self):
        compressor = SemanticCompressor()

        huge_log_output = "\n".join([f"2026-08-25 14:{i:02d}:00 INFO Health check status code 200" for i in range(50)])
        huge_log_output += "\n2026-08-25 14:55:00 ERROR 500 in /api/checkout: Database connection timeout."

        item = EvidenceItem(
            content=huge_log_output,
            reference=EvidenceReference(document_id="tool_out_logs", chunk_id="chunk_logs"),
        )

        compressed = compressor.compress(item, target_token_budget=100)
        assert compressed.compressed_token_count < compressed.original_token_count
        assert "Database connection timeout" in compressed.compressed_text
