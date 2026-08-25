import pytest
from app.integrations.credentials import CredentialManager
from app.integrations.deployment import DeploymentPipeline, DeploymentEnvironment


class TestIntegrationSecurity:
    def test_cross_tenant_credential_leak_protection(self):
        cm = CredentialManager()
        meta = cm.register_credential(
            provider="AWS",
            secret_value="AKIAIOSFODNN7EXAMPLE",
            user_id="alice",
            tenant_id="tenant_alpha",
        )

        # Cross-tenant read must fail
        assert cm.resolve_raw_secret(meta.ref_id, user_id="alice", tenant_id="tenant_beta") is None

        # Cross-user read must fail
        assert cm.resolve_raw_secret(meta.ref_id, user_id="mallory", tenant_id="tenant_alpha") is None

    def test_production_deployment_blocked_without_approval(self):
        dp = DeploymentPipeline()
        dep = dp.create_deployment("billing-service", "v2.0.0")

        # Promoting unverified deployment must fail
        promoted, msg = dp.promote_to_production(dep.deployment_id, approved=False)
        assert promoted is False
        assert "staging verification" in msg.lower()

        # Run staging validation
        dp.run_staging_validation(dep.deployment_id)

        # Promoting without explicit human approval must fail
        promoted2, msg2 = dp.promote_to_production(dep.deployment_id, approved=False)
        assert promoted2 is False
        assert "approval" in msg2.lower()

        # Promoting with approval succeeds
        promoted3, msg3 = dp.promote_to_production(dep.deployment_id, approved=True)
        assert promoted3 is True
        assert dep.environment == DeploymentEnvironment.PRODUCTION
