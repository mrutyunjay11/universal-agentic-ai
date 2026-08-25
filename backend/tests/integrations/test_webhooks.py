import pytest
import time
from app.integrations.webhooks import WebhookManager


class TestWebhooks:
    def test_hmac_signature_and_anti_replay_verification(self):
        wm = WebhookManager()
        payload = b'{"event": "pull_request.opened", "pr_id": 42}'
        secret = "super_secret_webhook_key"

        valid_sig = wm.generate_signature(payload, secret)

        # 1. Valid verification
        valid, reason = wm.verify_webhook_event(
            payload_bytes=payload,
            signature=valid_sig,
            secret=secret,
            timestamp=time.time(),
            delivery_id="deliv_101",
        )
        assert valid is True
        assert reason == "Valid"

        # 2. Replay attack attempt (duplicate delivery ID)
        replay_valid, replay_reason = wm.verify_webhook_event(
            payload_bytes=payload,
            signature=valid_sig,
            secret=secret,
            timestamp=time.time(),
            delivery_id="deliv_101",
        )
        assert replay_valid is False
        assert "replay attack" in replay_reason.lower()

        # 3. Invalid signature
        bad_valid, bad_reason = wm.verify_webhook_event(
            payload_bytes=payload,
            signature="sha256=invalidhex0000",
            secret=secret,
            timestamp=time.time(),
            delivery_id="deliv_102",
        )
        assert bad_valid is False
        assert "invalid" in bad_reason.lower()
