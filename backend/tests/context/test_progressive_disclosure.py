import pytest
from app.context.progressive import ProgressiveDisclosureEngine
from app.context.policies import ProgressiveLevel


class TestProgressiveDisclosure:
    def test_multi_level_on_demand_escalation(self):
        engine = ProgressiveDisclosureEngine()
        engine.register_document(
            document_id="doc_arch",
            title="System Architecture Guide",
            full_text="This document covers the complete 50-page architecture of the universal agent platform...",
            summary="High level overview of agent platform modular layers.",
            sections={"security": "Detailed security RBAC and secret vault specifications."},
        )

        # Fetch Level 0 (Metadata)
        meta = engine.fetch_at_level("doc_arch", ProgressiveLevel.METADATA)
        assert meta is not None
        assert "Metadata" in meta.content

        # Fetch Level 1 (Summary)
        summary = engine.fetch_at_level("doc_arch", ProgressiveLevel.SUMMARY)
        assert summary is not None
        assert "overview" in summary.content

        # Fetch Level 3 (Section)
        section = engine.fetch_at_level("doc_arch", ProgressiveLevel.SECTION, section_name="security")
        assert section is not None
        assert "RBAC" in section.content
