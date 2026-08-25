from __future__ import annotations
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.schemas import PermissionTier, generate_session_id
from app.services.session_manager import session_manager
from app.services.agent_state_machine import agent_machine
from app.services.terminal_service import terminal_manager
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    def get(self, session_id: str):
        return self._connections.get(session_id)

    async def send_json(self, session_id: str, data: dict):
        ws = self.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(session_id)

    async def broadcast(self, data: dict):
        for session_id in list(self._connections.keys()):
            await self.send_json(session_id, data)


connection_manager = ConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await connection_manager.connect(session_id, websocket)

    session = session_manager.get_session(session_id)
    if not session:
        session = session_manager.create_session()
        await connection_manager.send_json(session_id, {
            "type": "session_created",
            "session_id": session_id,
        })

    await connection_manager.send_json(session_id, {
        "type": "connected",
        "session_id": session_id,
    })

    def on_state_change(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "state_change",
                "data": data,
            })
        )

    def on_stream(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "stream",
                "data": data,
            })
        )

    def on_tool_exec(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "tool_execution",
                "data": {
                    "tool": data.tool,
                    "success": data.success,
                    "output": str(data.output)[:1000] if data.output else None,
                    "error": data.error,
                    "duration_ms": data.duration_ms,
                },
            })
        )

    def on_approval(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "approval_required",
                "data": data,
            })
        )

    def on_done(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "done",
                "data": data,
            })
        )

    def on_error(data: Any):
        asyncio.ensure_future(
            connection_manager.send_json(session_id, {
                "type": "error",
                "data": data,
            })
        )

    agent_machine.on("state_change", on_state_change)
    agent_machine.on("stream", on_stream)
    agent_machine.on("tool_execution", on_tool_exec)
    agent_machine.on("approval", on_approval)
    agent_machine.on("done", on_done)
    agent_machine.on("error", on_error)

    import asyncio

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "message":
                user_message = data.get("message", "")
                project_id = data.get("project_id")
                project_root = data.get("project_root", "./projects")
                permission = PermissionTier(
                    data.get("permission", "read_write")
                )

                await session_manager.save_message(
                    session_id, "user", user_message
                )

                asyncio.create_task(
                    agent_machine.start(
                        user_message=user_message,
                        project_id=project_id,
                        project_root=project_root,
                        session_id=session_id,
                        permission=permission,
                    )
                )

            elif msg_type == "approval":
                approved = data.get("approved", False)
                reason = data.get("reason")
                asyncio.create_task(
                    agent_machine.approve_action(approved, reason)
                )

            elif msg_type == "cancel":
                agent_machine.cancel()
                await connection_manager.send_json(session_id, {
                    "type": "cancelled",
                })

            elif msg_type == "terminal_output":
                terminal_session = terminal_manager.get_session(session_id)
                if terminal_session and terminal_session.running:
                    lines = []
                    while True:
                        try:
                            line = await asyncio.wait_for(
                                terminal_session.stream_output(), timeout=0.1
                            )
                            lines.append(line)
                        except asyncio.TimeoutError:
                            break
                    if lines:
                        await connection_manager.send_json(session_id, {
                            "type": "terminal_output",
                            "data": {"output": "\n".join(lines)},
                        })

            elif msg_type == "ping":
                await connection_manager.send_json(session_id, {
                    "type": "pong",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        connection_manager.disconnect(session_id)
        terminal_manager.close_session(session_id)
