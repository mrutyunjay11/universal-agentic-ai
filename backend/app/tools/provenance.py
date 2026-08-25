from __future__ import annotations
import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    WEB_PAGE = "web_page"
    DOCUMENT = "document"
    CODE_FILE = "code_file"
    GIT_COMMIT = "git_commit"
    DATABASE = "database"
    API_RESPONSE = "api_response"
    CALCULATION = "calculation"
    SYSTEM_DIAGNOSTIC = "system_diagnostic"
    USER_INPUT = "user_input"


class ProvenanceRecord(BaseModel):
    """
    Standardized Source Provenance metadata for information-retrieval and research tools.
    Enables evidence attribution and answering 'where did this information come from?'.
    """
    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:8]}")
    source_type: SourceType
    uri: str
    title: Optional[str] = None
    publisher_or_author: Optional[str] = None
    publication_date: Optional[str] = None
    retrieval_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_hash: Optional[str] = None
    parent_source_id: Optional[str] = None
    extraction_method: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return self.model_dump()


def compute_content_hash(content: str | bytes) -> str:
    """Computes a SHA-256 hash formatted as 'sha256:...'."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def create_provenance(
    source_type: SourceType,
    uri: str,
    content: Optional[str | bytes] = None,
    title: Optional[str] = None,
    publisher_or_author: Optional[str] = None,
    publication_date: Optional[str] = None,
    parent_source_id: Optional[str] = None,
    extraction_method: Optional[str] = None,
    confidence: float = 1.0,
) -> ProvenanceRecord:
    """Convenience helper to construct a verified ProvenanceRecord."""
    content_hash = compute_content_hash(content) if content is not None else None
    return ProvenanceRecord(
        source_type=source_type,
        uri=uri,
        title=title,
        publisher_or_author=publisher_or_author,
        publication_date=publication_date,
        content_hash=content_hash,
        parent_source_id=parent_source_id,
        extraction_method=extraction_method,
        confidence=confidence,
    )
