import pytest
from app.integrations.connectors.email import email_connector
from app.integrations.base import IntegrationContext


class TestEmailIntegration:
    @pytest.mark.asyncio
    async def test_email_draft_and_send_with_reconciliation(self):
        ctx = IntegrationContext()
        draft = await email_connector.execute(
            "draft_message",
            ctx,
            to="partner@example.com",
            subject="Integration Proposal",
        )
        assert draft.status == "SUCCESS"
        assert draft.data["status"] == "DRAFTED"

        sent = await email_connector.execute(
            "send_message",
            ctx,
            to="partner@example.com",
            subject="Integration Proposal",
        )
        assert sent.status == "SUCCESS"
        assert sent.data["verified_delivery"] is True
        assert sent.reconciliation_state["delivered"] is True
