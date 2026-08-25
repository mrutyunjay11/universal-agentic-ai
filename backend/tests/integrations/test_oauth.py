import pytest
from app.integrations.oauth import OAuthFramework


class TestOAuthFramework:
    def test_oauth_auth_url_and_code_exchange(self):
        oauth = OAuthFramework()

        res = oauth.generate_authorization_url(
            provider="Google",
            client_id="client_google_123",
            redirect_uri="https://app.example.com/oauth/callback",
            scopes=["email.read", "calendar.read"],
            user_id="user_charlie",
            tenant_id="tenant_main",
        )

        assert "authorization_url" in res
        assert "state" in res
        assert "auth.google.com" in res["authorization_url"]

        # Exchange auth code
        exchange = oauth.verify_and_exchange_code(
            state=res["state"],
            code="auth_code_xyz987",
        )

        assert exchange is not None
        assert exchange["status"] == "AUTHENTICATED"
        assert exchange["credential_reference"].startswith("cred_google_")
        assert "calendar.read" in exchange["scopes"]
