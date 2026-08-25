import pytest
from app.memory.provenance import MemoryProvenanceManager
from app.memory.models import MemoryRecord, VerificationStatus


class TestMemoryProvenance:
    def test_provenance_attachment_and_validation(self):
        record = MemoryRecord(content="FastAPI is an asynchronous web framework")

        # 1. Attach source
        MemoryProvenanceManager.attach_source(
            record,
            source_uri="https://fastapi.tiangolo.com",
            source_id="src_fastapi_docs",
            source_content="FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints.",
        )
        assert record.source == "https://fastapi.tiangolo.com"
        assert "src_fastapi_docs" in record.source_ids
        assert "source_content_hash" in record.metadata

        # 2. Attach verification
        MemoryProvenanceManager.attach_verification_result(
            record,
            verdict="verified",
            confidence=0.98,
            evidence_sources=[{"uri": "https://fastapi.tiangolo.com"}],
        )
        assert record.verification_status == VerificationStatus.VERIFIED
        assert record.confidence == 0.98

        # 3. Integrity check
        valid, msg = MemoryProvenanceManager.verify_provenance_integrity(record)
        assert valid is True
