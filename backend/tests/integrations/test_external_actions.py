import pytest
from app.integrations.policies import ExternalActionApprovalManager, ApprovalState


class TestExternalActions:
    def test_approval_denial_lifecycle(self):
        mgr = ExternalActionApprovalManager()
        act = mgr.create_preview(
            action_type="delete_database_table",
            provider="DatabaseGateway",
            target_resource="users_archive_2025",
            parameters={},
            risk_level="CRITICAL",
            requires_approval=True,
        )

        assert act.approval_state == ApprovalState.PENDING

        mgr.deny_action(act.id)
        assert mgr.get_action(act.id).approval_state == ApprovalState.DENIED
