from __future__ import annotations
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Patterns for sensitive credentials to redact
_SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|auth[_-]?token|access[_-]?token|private[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"), r"\1=***REDACTED***"),
    (re.compile(r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{16,})"), r"\1***REDACTED***"),
    (re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"), r"***REDACTED_PRIVATE_KEY***"),
    (re.compile(r"(?i)(postgres|mysql|mongodb|redis)://([^:]+):([^@]+)@"), r"\1://\2:***REDACTED***@"),
    (re.compile(r"(?i)ghp_[a-zA-Z0-9]{36}"), r"ghp_***REDACTED***"),
    (re.compile(r"(?i)sk-[a-zA-Z0-9]{20,}"), r"sk-***REDACTED***"),
]


def redact_secrets(data: Any) -> Any:
    """
    Recursively scans and redacts sensitive credentials from strings, dicts, lists, and objects.
    """
    if isinstance(data, str):
        redacted = data
        for pattern, replacement in _SECRET_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    elif isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("password", "secret", "token", "api_key", "private_key", "authorization")):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = redact_secrets(v)
        return sanitized
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_secrets(item) for item in data)
    return data


class AuditEvent(BaseModel):
    """Execution event record for audit logging and observability."""
    event_id: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool_name: str
    category: str
    permission: str
    duration_ms: int = 0
    success: bool = True
    input_args: dict[str, Any] = Field(default_factory=dict)
    output_summary: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    user_approved: bool = True


class AuditLogger:
    """Central audit logger that records sanitized tool executions."""
    def __init__(self, log_file: Optional[str] = None, max_in_memory: int = 500):
        self.log_file = log_file
        self.max_in_memory = max_in_memory
        self._history: list[AuditEvent] = []

    def record(
        self,
        tool_name: str,
        category: str,
        permission: str,
        duration_ms: int,
        success: bool,
        input_args: dict[str, Any],
        output: Any = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
        user_approved: bool = True,
    ) -> AuditEvent:
        sanitized_input = redact_secrets(input_args)
        output_str = ""
        if output is not None:
            output_redacted = redact_secrets(output)
            output_str = str(output_redacted)[:300] if not isinstance(output_redacted, str) else output_redacted[:300]

        event = AuditEvent(
            tool_name=tool_name,
            category=category,
            permission=permission,
            duration_ms=duration_ms,
            success=success,
            input_args=sanitized_input if isinstance(sanitized_input, dict) else {"data": sanitized_input},
            output_summary=output_str,
            error=str(error) if error else None,
            session_id=session_id,
            user_approved=user_approved,
        )

        self._history.append(event)
        if len(self._history) > self.max_in_memory:
            self._history.pop(0)

        if self.log_file:
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(event.model_dump_json() + "\n")
            except Exception as e:
                logger.warning("Failed to write to audit log file %s: %s", self.log_file, e)

        return event

    def get_events(self, limit: int = 50, tool_name: Optional[str] = None) -> list[AuditEvent]:
        events = self._history
        if tool_name:
            events = [e for e in events if e.tool_name == tool_name]
        return events[-limit:]

    def clear(self):
        self._history.clear()


audit_logger = AuditLogger(log_file="./audit_events.jsonl")
