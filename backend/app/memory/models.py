from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"
    PROJECT = "PROJECT"
    USER_PREFERENCE = "USER_PREFERENCE"
    FACT = "FACT"
    TASK_HISTORY = "TASK_HISTORY"
    SOURCE_MEMORY = "SOURCE_MEMORY"


class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


class FreshnessStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    CONTRADICTED = "CONTRADICTED"


class MemoryScope(str, Enum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    SESSION = "SESSION"
    TASK = "TASK"
    USER = "USER"


class MemoryRecord(BaseModel):
    """
    Standardized, strongly-typed memory record for persistent, episodic, semantic,
    procedural, project, and task-scoped memory.
    """
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    memory_type: MemoryType = MemoryType.SEMANTIC
    scope: MemoryScope = MemoryScope.GLOBAL
    content: str = Field(..., description="Main factual or procedural content of the memory")
    summary: Optional[str] = None
    
    # Provenance attribution
    source: Optional[str] = None
    source_ids: list[str] = Field(default_factory=list)
    
    # Context & isolation keys
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Timestamps (ISO 8601 UTC)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0
    
    # Separate multi-factor signals (not collapsed into a single number)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Verification & Lifecycle
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    freshness_status: FreshnessStatus = FreshnessStatus.CURRENT
    expires_at: Optional[str] = None
    superseded_by: Optional[str] = None
    
    # Versioning & metadata
    version: int = 1
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Vector embedding representation (optional)
    embedding: Optional[list[float]] = None

    def mark_accessed(self):
        """Updates last_accessed_at and increments access_count."""
        self.last_accessed_at = datetime.now(timezone.utc).isoformat()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class InvalidationRecord(BaseModel):
    """Audit trail record for a modified, superseded, or invalidated memory."""
    id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:8]}")
    memory_id: str
    previous_status: FreshnessStatus
    new_status: FreshnessStatus
    reason: str
    superseded_by: Optional[str] = None
    actor: str = "system"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
