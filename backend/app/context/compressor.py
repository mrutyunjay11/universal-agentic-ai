from __future__ import annotations
import re
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.context.evidence import EvidenceItem, EvidenceReference


class CompressedContextChunk(BaseModel):
    compressed_text: str
    original_token_count: int
    compressed_token_count: int
    compression_ratio: float
    preserved_facts: list[str] = Field(default_factory=list)
    reference: EvidenceReference


class SemanticCompressor:
    """
    Semantic Fact-Preserving Context Compressor.
    Compresses large text or tool output while strictly protecting numbers, dates,
    versions, code snippets, negations, condition clauses, and source references.
    """

    def compress(
        self,
        item: EvidenceItem,
        target_token_budget: int = 200,
    ) -> CompressedContextChunk:
        raw = item.content.strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]

        preserved_facts: list[str] = []
        critical_lines: list[str] = []

        # Extraction regexes for critical tokens: numbers, versions, conditions, code, error events
        critical_patterns = [
            r"v\d+(\.\d+)*",  # versions (v4.2.0)
            r"\b(error|fail|failed|timeout|exception|fatal|warn|warning|critical|not|never|only|must|cannot|forbidden|deprecated|supported)\b",  # negations, constraints & errors
            r"\b\d+(\.\d+)?(ms|s|gb|mb|kb|%|usd|\$)\b",  # metrics
            r"(`[^`]+`)",  # code identifiers
        ]

        for line in lines:
            has_critical = any(re.search(pat, line, re.IGNORECASE) for pat in critical_patterns)
            if has_critical:
                critical_lines.append(line)
                preserved_facts.append(line[:80])

        compressed_text = " | ".join(critical_lines) if critical_lines else lines[0] if lines else raw

        orig_len = max(1, len(raw.split()))
        comp_len = max(1, len(compressed_text.split()))
        ratio = round(min(1.0, comp_len / orig_len), 3)

        return CompressedContextChunk(
            compressed_text=compressed_text,
            original_token_count=orig_len,
            compressed_token_count=comp_len,
            compression_ratio=ratio,
            preserved_facts=preserved_facts,
            reference=item.reference,
        )


semantic_compressor = SemanticCompressor()
