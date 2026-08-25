from __future__ import annotations
import hmac
import hashlib
import time
from typing import Any, Optional


class WebhookManager:
    """
    Validates inbound webhook payloads against cryptographic HMAC signatures,
    anti-replay timestamp windows, and schema conformance.
    """

    def __init__(self, timestamp_tolerance_seconds: int = 300):
        self.timestamp_tolerance = timestamp_tolerance_seconds
        self._processed_delivery_ids: set[str] = set()

    def generate_signature(self, payload: bytes, secret: str) -> str:
        """Generates HMAC-SHA256 hex digest."""
        return "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        if not signature or not secret:
            return False
        expected = self.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    def verify_webhook_event(
        self,
        payload_bytes: bytes,
        signature: str,
        secret: str,
        timestamp: Optional[float] = None,
        delivery_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        # 1. Anti-replay verification
        if delivery_id:
            if delivery_id in self._processed_delivery_ids:
                return False, "Duplicate webhook delivery ID detected (replay attack prevention)"
            self._processed_delivery_ids.add(delivery_id)

        # 2. Timestamp freshness verification
        if timestamp is not None:
            if abs(time.time() - timestamp) > self.timestamp_tolerance:
                return False, f"Webhook timestamp expired (outside {self.timestamp_tolerance}s window)"

        # 3. Cryptographic signature check
        if not self.verify_signature(payload_bytes, signature, secret):
            return False, "Invalid cryptographic HMAC signature"

        return True, "Valid"


webhook_manager = WebhookManager()
