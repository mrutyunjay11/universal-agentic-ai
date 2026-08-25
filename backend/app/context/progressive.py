from __future__ import annotations
from typing import Any, Optional
from app.context.policies import ProgressiveLevel
from app.context.evidence import EvidenceItem, EvidenceReference


class ProgressiveDisclosureEngine:
    """
    Progressive Disclosure Engine.
    Dynamically escalates evidence detail from Level 0 (Metadata) up to Level 4 (Full Document)
    on demand, preventing premature context bloat.
    """

    def __init__(self):
        self._document_store: dict[str, dict[str, Any]] = {}

    def register_document(
        self,
        document_id: str,
        title: str,
        full_text: str,
        summary: str,
        sections: dict[str, str],
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self._document_store[document_id] = {
            "document_id": document_id,
            "title": title,
            "full_text": full_text,
            "summary": summary,
            "sections": sections,
            "metadata": metadata or {},
        }

    def fetch_at_level(
        self,
        document_id: str,
        level: ProgressiveLevel,
        section_name: Optional[str] = None,
    ) -> Optional[EvidenceItem]:
        doc = self._document_store.get(document_id)
        if not doc:
            return None

        content = ""
        if level == ProgressiveLevel.METADATA:
            content = f"Document: {doc['title']} | ID: {document_id} | Metadata: {doc['metadata']}"
        elif level == ProgressiveLevel.SUMMARY:
            content = f"Summary of {doc['title']}: {doc['summary']}"
        elif level == ProgressiveLevel.EXCERPT:
            content = doc['summary']
            if section_name and section_name in doc['sections']:
                content = doc['sections'][section_name][:300] + "..."
        elif level == ProgressiveLevel.SECTION:
            content = doc['sections'].get(section_name or list(doc['sections'].keys())[0], doc['full_text'][:1000])
        elif level == ProgressiveLevel.FULL_DOC:
            content = doc['full_text']

        ref = EvidenceReference(
            document_id=document_id,
            chunk_id=f"{document_id}_lvl_{level.value}",
            section=section_name,
            content_hash=f"hash_{document_id}",
        )

        return EvidenceItem(
            content=content,
            reference=ref,
            progressive_level=level,
            authoritative_score=0.9,
        )


progressive_engine = ProgressiveDisclosureEngine()
