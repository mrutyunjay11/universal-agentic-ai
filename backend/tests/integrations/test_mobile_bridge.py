import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.integrations.mobile_bridge import (
    mobile_bridge,
    MobileCommandRequest,
    MobileApprovalRequest,
    MobileChannel,
    MobileApprovalAction,
)
from app.agent.state import TaskState


class TestMobileBridge:
    @pytest.mark.asyncio
    async def test_mobile_command_execution_pwa_text(self):
        req = MobileCommandRequest(
            channel=MobileChannel.PWA_TEXT,
            prompt="Search web for latest AI news and summarize",
            user_id="mobile_user_01",
        )
        res = await mobile_bridge.execute_mobile_command(req)
        assert res.command_id == req.id
        assert res.status == TaskState.COMPLETED
        assert "Search web for latest AI news" in res.output or len(res.tools_used) > 0

    @pytest.mark.asyncio
    async def test_mobile_command_voice_transcribed(self):
        req = MobileCommandRequest(
            channel=MobileChannel.PWA_VOICE,
            prompt="Run automated test suite and check code health",
            user_id="mobile_user_01",
            voice_transcribed=True,
        )
        res = await mobile_bridge.execute_mobile_command(req)
        assert res.status == TaskState.COMPLETED
        assert res.completed_at is not None

    def test_mobile_approval_lifecycle(self):
        # Register a high-impact action requiring mobile confirmation
        approval_id = mobile_bridge.register_approval_request(
            task_id="task_123",
            tool="stripe_checkout",
            args={"amount": 49.99, "currency": "USD"},
            description="Process subscription purchase of $49.99",
        )
        assert approval_id.startswith("appr_")

        # Process approval from mobile
        appr_req = MobileApprovalRequest(
            approval_id=approval_id,
            action=MobileApprovalAction.APPROVE,
            user_id="mobile_user_01",
        )
        result = mobile_bridge.process_mobile_approval(appr_req)
        assert result["success"] is True
        assert result["status"] == "APPROVED"

    def test_telegram_message_formatting(self):
        approval_id = mobile_bridge.register_approval_request(
            task_id="task_456",
            tool="deploy_production",
            args={"env": "prod"},
            description="Deploy release v1.0.0 to production",
        )
        cmd_res = mobile_bridge.execute_mobile_command  # helper check
        from app.integrations.mobile_bridge import MobileCommandResponse

        mock_resp = MobileCommandResponse(
            command_id="cmd_test",
            task_id="task_456",
            status=TaskState.COMPLETED,
            summary="Deployment prepared",
            output="Ready to deploy to prod cluster",
            tools_used=["docker", "k8s"],
            requires_approval=True,
            pending_approval_id=approval_id,
        )
        tg_msg = mobile_bridge.format_telegram_message(mock_resp)
        assert "🤖 *Universal Agentic AI*" in tg_msg["text"]
        assert tg_msg["reply_markup"] is not None
        assert len(tg_msg["reply_markup"]["inline_keyboard"][0]) == 2


class TestMobileRouterEndpoints:
    @pytest.mark.asyncio
    async def test_mobile_status_and_config_endpoints(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/api/mobile/status")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ready"
            assert "PWA_VOICE" in data["supported_channels"]

            config_res = await client.get("/api/mobile/config")
            assert config_res.status_code == 200
            config_data = config_res.json()
            assert config_data["pwa_manifest"] == "/manifest.json"

    @pytest.mark.asyncio
    async def test_mobile_command_api_endpoint(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "channel": "PWA_VOICE",
                "prompt": "Check server health metrics and memory consumption",
                "user_id": "mobile_user_02",
                "voice_transcribed": True,
            }
            res = await client.post("/api/mobile/command", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "COMPLETED"
            assert "tools_used" in data

    @pytest.mark.asyncio
    async def test_telegram_webhook_endpoint(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test /start command
            start_payload = {
                "message": {
                    "text": "/start",
                    "from": {"id": 12345678, "username": "mobile_tester"},
                }
            }
            res = await client.post("/api/mobile/telegram/webhook", json=start_payload)
            assert res.status_code == 200
            data = res.json()
            assert "Welcome to Universal Agentic AI Mobile Bot" in data["text"]

            # Test regular instruction message
            msg_payload = {
                "message": {
                    "text": "Scrape the top news headlines",
                    "from": {"id": 12345678, "username": "mobile_tester"},
                }
            }
            msg_res = await client.post("/api/mobile/telegram/webhook", json=msg_payload)
            assert msg_res.status_code == 200
            msg_data = msg_res.json()
            assert "🤖 *Universal Agentic AI*" in msg_data["text"]
