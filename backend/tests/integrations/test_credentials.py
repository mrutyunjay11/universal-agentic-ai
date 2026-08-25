import pytest
from app.integrations.credentials import CredentialManager
from app.integrations.secrets import SecretStore


class TestCredentials:
    def test_opaque_reference_and_vault_isolation(self):
        cm = CredentialManager()
        meta = cm.register_credential(
            provider="GitHub",
            secret_value="ghp_super_secret_token_12345",
            user_id="user_alice",
            tenant_id="tenant_acme",
            scopes=["github.read", "github.write"],
        )

        assert meta.ref_id.startswith("cred_github_")
        assert meta.user_id == "user_alice"

        # Resolve secret for matching user
        secret = cm.resolve_raw_secret(meta.ref_id, user_id="user_alice", tenant_id="tenant_acme")
        assert secret == "ghp_super_secret_token_12345"

        # Cross-user access attempt must be blocked
        cross_user = cm.resolve_raw_secret(meta.ref_id, user_id="user_bob", tenant_id="tenant_acme")
        assert cross_user is None

        # Cross-tenant access attempt must be blocked
        cross_tenant = cm.resolve_raw_secret(meta.ref_id, user_id="user_alice", tenant_id="tenant_other")
        assert cross_tenant is None
