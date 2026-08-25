import pytest
from app.platform.security_hardener import SecurityHardener, AuthenticatedPrincipal, IdentityType


class TestSecurityHardener:
    def test_identity_authorization_and_egress_allowlists(self):
        sh = SecurityHardener()

        # Regular user principal
        user_p = AuthenticatedPrincipal(
            principal_id="usr_123",
            identity_type=IdentityType.HUMAN_USER,
            roles=["user"],
        )

        assert sh.authorize_action(user_p, "run_tool") is True
        assert sh.authorize_action(user_p, "system:restart_cluster") is False

        # Admin principal
        admin_p = AuthenticatedPrincipal(
            principal_id="adm_001",
            identity_type=IdentityType.ADMINISTRATOR,
            roles=["admin"],
        )
        assert sh.authorize_action(admin_p, "system:restart_cluster") is True

        # Egress validation
        assert sh.validate_egress_domain("api.github.com") is True
        assert sh.validate_egress_domain("subdomain.amazonaws.com") is True
        assert sh.validate_egress_domain("malicious-exfiltration-target.ru") is False
