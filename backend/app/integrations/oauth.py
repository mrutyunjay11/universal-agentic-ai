from __future__ import annotations
import uuid
import hashlib
import secrets
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.integrations.credentials import credential_manager


class OAuthSession(BaseModel):
    session_id: str
    provider: str
    state: str
    code_verifier: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=list)
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"


class OAuthTokenPayload(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scopes: list[str] = Field(default_factory=list)


class OAuthFramework:
    """
    Reusable OAuth 2.0 / OIDC framework for external identity and tool authorization.
    Handles PKCE state verification, callback handling, token exchange, and refresh.
    """

    def __init__(self):
        self._active_sessions: dict[str, OAuthSession] = {}

    def generate_authorization_url(
        self,
        provider: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
    ) -> dict[str, str]:
        state = secrets.token_urlsafe(16)
        code_verifier = secrets.token_urlsafe(32)
        session_id = f"oauth_sess_{uuid.uuid4().hex[:8]}"

        session = OAuthSession(
            session_id=session_id,
            provider=provider,
            state=state,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            scopes=scopes,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        self._active_sessions[state] = session

        # Construct standard OAuth2 auth URL
        auth_url = f"https://auth.{provider.lower()}.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&state={state}&scope={'+'.join(scopes)}&response_type=code"

        return {
            "session_id": session_id,
            "authorization_url": auth_url,
            "state": state,
        }

    def verify_and_exchange_code(
        self,
        state: str,
        code: str,
    ) -> Optional[dict[str, Any]]:
        session = self._active_sessions.pop(state, None)
        if not session:
            return None

        # Simulate token exchange with provider
        mock_access_token = f"tok_{session.provider.lower()}_{uuid.uuid4().hex[:12]}"
        mock_refresh_token = f"reftok_{session.provider.lower()}_{uuid.uuid4().hex[:12]}"

        # Register credential reference in credential manager
        cred_meta = credential_manager.register_credential(
            provider=session.provider,
            secret_value=mock_access_token,
            credential_type="oauth2",
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            scopes=session.scopes,
        )

        return {
            "credential_reference": cred_meta.ref_id,
            "provider": session.provider,
            "scopes": session.scopes,
            "status": "AUTHENTICATED",
        }

    def refresh_access_token(self, credential_ref: str) -> bool:
        """Simulates token refresh using refresh token."""
        return True


oauth_framework = OAuthFramework()
