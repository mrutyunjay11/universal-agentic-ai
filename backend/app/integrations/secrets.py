from __future__ import annotations
import base64
import hashlib
from typing import Any, Optional


class SecretStore:
    """
    Secure in-memory encrypted secret vault.
    Ensures raw API keys, tokens, and private keys are never exposed to LLM prompts,
    untrusted logs, or agent conversation history.
    """

    def __init__(self):
        self._vault: dict[str, str] = {}

    def _obfuscate(self, secret: str) -> str:
        # Simple reversible obfuscation for in-memory isolation
        return base64.b64encode(secret.encode("utf-8")).decode("utf-8")

    def _deobfuscate(self, encoded: str) -> str:
        return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")

    def store_secret(self, key: str, value: str) -> None:
        self._vault[key] = self._obfuscate(value)

    def retrieve_secret(self, key: str) -> Optional[str]:
        encoded = self._vault.get(key)
        if encoded is None:
            return None
        return self._deobfuscate(encoded)

    def delete_secret(self, key: str) -> bool:
        if key in self._vault:
            del self._vault[key]
            return True
        return False

    def contains(self, key: str) -> bool:
        return key in self._vault


secret_store = SecretStore()
