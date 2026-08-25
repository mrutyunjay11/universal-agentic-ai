import pytest
from app.integrations.rate_limits import RateLimitManager


class TestRateLimits:
    def test_token_bucket_rate_limiting(self):
        rl = RateLimitManager()
        rl.configure_provider("Slack", max_requests_per_minute=2)

        # 1st call -> OK
        assert rl.check_and_consume("Slack", cost=1.0) is True
        # 2nd call -> OK
        assert rl.check_and_consume("Slack", cost=1.0) is True
        # 3rd call immediately -> Exceeded
        assert rl.check_and_consume("Slack", cost=1.0) is False
