from __future__ import annotations
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from app.models.schemas import ChatRequest, ChatResponse, generate_session_id
from app.services.ollama_client import ollama_client
from app.services.context_manager import context_manager
from app.services.session_manager import session_manager
from app.services.tool_call_parser import parse_tool_call, validate_tool_call
from app.services.agent_state_machine import agent_machine
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)
router = APIRouter()


class SimpleChatRequest(BaseModel):
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    message: str
    stream: bool = True


@router.post("/chat", response_model=ChatResponse)
async def chat(request: SimpleChatRequest):
    session_id = request.session_id or generate_session_id()
    session = session_manager.get_session(session_id)
    if not session:
        session = session_manager.create_session(request.project_id)

    await session_manager.save_message(session_id, "user", request.message)

    system_prompt, messages = context_manager.prepare_prompt(
        user_message=request.message,
        conversation_history=session.messages,
        tool_schemas=tool_registry.get_schemas(),
    )

    if request.stream:
        return EventSourceResponse(
            _stream_response(session_id, messages),
            media_type="text/event-stream",
        )

    try:
        result = await ollama_client.chat(
            model="qwen2.5-coder:32b",
            messages=messages,
        )
        response_text = result.get("message", {}).get("content", "")

        parsed = parse_tool_call(response_text)
        if parsed.is_tool_call:
            validation_error = validate_tool_call(parsed, tool_registry.get_tool_names())
            if validation_error:
                response_text = f"I need to use a tool: {parsed.tool} with args {parsed.args}"
            else:
                tool_result = await tool_registry.execute(
                    parsed.tool, parsed.args
                )
                await session_manager.save_message(
                    session_id, "assistant", response_text,
                    tool_calls=[{"tool": parsed.tool, "args": parsed.args}],
                    tool_result={"success": tool_result.success, "output": str(tool_result.output)[:500]},
                )
                return ChatResponse(
                    session_id=session_id,
                    message=response_text,
                    tool_calls=[{"tool": parsed.tool, "args": parsed.args}],
                )

        await session_manager.save_message(session_id, "assistant", response_text)
        return ChatResponse(
            session_id=session_id,
            message=response_text,
        )
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_response(session_id: str, messages: list[dict]):
    try:
        async for chunk in ollama_client.chat_stream(
            model="qwen2.5-coder:32b",
            messages=messages,
        ):
            if "message" in chunk and "content" in chunk["message"]:
                content = chunk["message"]["content"]
                yield {"event": "token", "data": json.dumps({"token": content})}
            if chunk.get("done", False):
                break

        yield {"event": "done", "data": json.dumps({"session_id": session_id})}
    except Exception as e:
        logger.error("Stream error: %s", e)
        yield {"event": "error", "data": json.dumps({"error": str(e)})}
