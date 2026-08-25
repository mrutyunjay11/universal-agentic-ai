import pytest
from app.integrations.policies import IntegrationScope, ExternalActionApprovalManager, ApprovalState


class TestPermissionsAndApprovals:
    def test_external_action_preview_and_approval_flow(self):
        mgr = ExternalActionApprovalManager()

        preview = mgr.create_preview(
            action_type="send_email",
            provider="EmailGateway",
            target_resource="ceo@external-partner.com",
            parameters={"subject": "Confidential Partnership Agreement"},
            risk_level="HIGH",
            requires_approval=True,
        )

        assert preview.id.startswith("act_")
        assert preview.approval_state == ApprovalState.PENDING

        # Approve action
        assert mgr.approve_action(preview.id) is True
        updated = mgr.get_action(preview.id)
        assert updated.approval_state == ApprovalState.APPROVED
