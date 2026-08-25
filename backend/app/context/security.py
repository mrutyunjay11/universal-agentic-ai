from __future__ import annotations
import re
from typing import Any


class ContextSecuritySanitizer:
    """
    Context Security & Prompt Injection Isolator.
    Enforces clear boundaries between system instructions and untrusted external data.
    Performs secret token redaction prior to context insertion.
    """

    def __init__(self):
        self._secret_patterns = [
            r"ghp_[a-zA-Z0-9]{20,}",
            r"AKIA[0-9A-Z]{16}",
            r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
            r"password\s*=\s*['\"][^'\"]+['\"]",
        ]

    def sanitize_and_wrap(self, content: str, origin: str = "external_source") -> str:
        # 1. Redact secrets
        sanitized = content
        for pat in self._secret_patterns:
            sanitized = re.sub(pat, "[REDACTED_SECRET]", sanitized, flags=re.IGNORECASE)

        # 2. Wrap in explicit external data sandbox delimiters
        return f'<EXTERNAL_DATA origin="{origin}">\n{sanitized}\n</EXTERNAL_DATA>'


context_security = ContextSecuritySanitizer()
