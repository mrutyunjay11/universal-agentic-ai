from __future__ import annotations
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from app.integrations.mobile_bridge import (
    mobile_bridge,
    MobileCommandRequest,
    MobileCommandResponse,
    MobileApprovalRequest,
    MobileChannel,
    MobileApprovalAction,
)

logger = logging.getLogger("universal_agent.routers.mobile")

router = APIRouter(prefix="/api/mobile", tags=["Mobile & Remote Control"])


@router.post("/command", response_model=MobileCommandResponse)
async def handle_mobile_command(request: MobileCommandRequest) -> MobileCommandResponse:
    """
    Executes a natural language or voice-transcribed command from a mobile device (PWA/iOS/Android).
    """
    try:
        return await mobile_bridge.execute_mobile_command(request)
    except Exception as e:
        logger.error(f"Mobile command failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_mobile_status() -> dict[str, Any]:
    """
    Returns platform readiness and pending approval counts for mobile home-screen widgets.
    """
    pending_count = sum(
        1 for a in mobile_bridge._pending_approvals.values() if a.get("status") == "PENDING"
    )
    return {
        "status": "ready",
        "platform": "Universal Agentic AI",
        "pending_approvals": pending_count,
        "supported_channels": [c.value for c in MobileChannel],
        "active_models": ["Qwen3.8-Max", "Qwen3-Embedding-8B", "Qwen3-Reranker-8B"],
    }


@router.post("/approve")
async def handle_mobile_approval(request: MobileApprovalRequest) -> dict[str, Any]:
    """
    Processes a 1-tap approval action from mobile notifications or Telegram inline buttons.
    """
    result = mobile_bridge.process_mobile_approval(request)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to resolve approval"))
    return result


@router.post("/telegram/webhook")
async def handle_telegram_webhook(request: Request) -> dict[str, Any]:
    """
    Receives incoming messages and callback button presses from Telegram Mobile Bot.
    """
    try:
        payload = await request.json()
        logger.info(f"Received Telegram webhook payload: {payload}")

        # Handle callback query (inline button click like Approve/Reject)
        if "callback_query" in payload:
            cb = payload["callback_query"]
            data = cb.get("data", "")
            if ":" in data:
                action_str, approval_id = data.split(":", 1)
                action = (
                    MobileApprovalAction.APPROVE
                    if action_str == "approve"
                    else MobileApprovalAction.REJECT
                )
                res = mobile_bridge.process_mobile_approval(
                    MobileApprovalRequest(approval_id=approval_id, action=action)
                )
                return {"status": "ok", "callback_processed": res}

        # Handle regular message text from Telegram
        if "message" in payload:
            msg = payload["message"]
            text = msg.get("text", "")
            user_id = str(msg.get("from", {}).get("id", "telegram_user"))

            if text.startswith("/start"):
                return {
                    "text": "👋 Welcome to Universal Agentic AI Mobile Bot! Send me any task or voice note to begin.",
                    "parse_mode": "Markdown",
                }

            cmd_req = MobileCommandRequest(
                channel=MobileChannel.TELEGRAM,
                prompt=text,
                user_id=user_id,
            )
            response = await mobile_bridge.execute_mobile_command(cmd_req)
            return mobile_bridge.format_telegram_message(response)

        return {"status": "ignored"}
    except Exception as e:
        logger.error(f"Telegram webhook handling error: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/config")
async def get_mobile_config() -> dict[str, Any]:
    """
    Returns mobile connection parameters, PWA manifest links, and Telegram bot instructions.
    """
    return {
        "pwa_manifest": "/manifest.json",
        "voice_dictation": "Web Speech API enabled",
        "telegram_setup": {
            "instructions": "Set TELEGRAM_BOT_TOKEN in .env and configure webhook to /api/mobile/telegram/webhook",
        },
        "apple_shortcuts": {
            "endpoint": "/api/mobile/command",
            "method": "POST",
            "payload_format": {"prompt": "Your voice/text instruction", "channel": "REST_API"},
        },
    }
