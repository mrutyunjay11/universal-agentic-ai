import pytest
from app.context.compressor import SemanticCompressor
from app.context.evidence import EvidenceItem, EvidenceReference


class TestSemanticCompression:
    def test_fact_and_constraint_preservation_in_compression(self):
        comp = SemanticCompressor()

        raw_text = """
        This library was released in 2026.
        Important constraint: Feature X is supported only on version >= 4.2.0.
        Legacy endpoints cannot be accessed without API keys.
        General prose describing generic setup instructions that are not strictly necessary.
        """

        item = EvidenceItem(
            content=raw_text,
            reference=EvidenceReference(document_id="doc_test", chunk_id="chunk_1"),
        )

        res = comp.compress(item, target_token_budget=100)
        assert res.compression_ratio <= 1.0
        assert "version >= 4.2.0" in res.compressed_text
        assert "only" in res.compressed_text or "cannot" in res.compressed_text
        assert res.reference.document_id == "doc_test"
