import pytest
from app.integrations.connectors.calendar import calendar_connector
from app.integrations.base import IntegrationContext


class TestCalendarIntegration:
    @pytest.mark.asyncio
    async def test_find_free_time_and_create_event(self):
        ctx = IntegrationContext()
        free_slots = await calendar_connector.execute("find_free_time", ctx)
        assert free_slots.status == "SUCCESS"
        assert len(free_slots.data["available_slots"]) >= 1

        event = await calendar_connector.execute(
            "create_event",
            ctx,
            title="Design Review",
            start_time="2026-08-26T10:00:00Z",
        )
        assert event.status == "SUCCESS"
        assert event.data["status"] == "CONFIRMED"
