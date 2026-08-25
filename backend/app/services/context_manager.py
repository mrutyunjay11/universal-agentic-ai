from __future__ import annotations
import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class TokenBudgetExceeded(Exception):
    pass


class ContextManager:
    def __init__(self):
        self._system_prompt: Optional[str] = None
        self._max_context: int = settings.primary_model_ctx
        self._headroom: int = settings.token_budget_headroom
        self._rag_max_tokens: int = settings.rag_max_tokens
        self._system_prompt_max: int = settings.system_prompt_max_tokens
        self._sliding_window: int = settings.sliding_window_turns

    def set_system_prompt(self, prompt: str):
        self._system_prompt = prompt

    def get_available_context(self, rag_tokens: int = 0) -> int:
        return self._max_context - self._headroom - rag_tokens

    def compress_conversation(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> list[dict[str, Any]]:
        if len(messages) <= self._sliding_window:
            return messages

        keep = messages[-self._sliding_window :]
        logger.info(
            "Compressed conversation from %d to %d messages (sliding window)",
            len(messages),
            len(keep),
        )
        return keep

    def prepare_prompt(
        self,
        user_message: str,
        conversation_history: list[dict[str, Any]],
        rag_context: Optional[list[str]] = None,
        tool_schemas: Optional[list[dict]] = None,
        task_plan: Optional[list[dict]] = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        system_parts: list[str] = []
        if self._system_prompt:
            system_parts.append(self._system_prompt)

        if tool_schemas:
            system_parts.append(
                "Available tools:\n"
                + "\n".join(
                    f"- {s['name']}: {s['description']}"
                    for s in tool_schemas
                )
            )
            system_parts.append(
                "Respond with JSON: {\"tool\": \"name\", \"args\": {...}}"
                " for tool calls, or plain text for normal responses."
            )

        if rag_context:
            rag_text = "\n\n".join(rag_context)
            system_parts.append(f"Relevant context:\n{rag_text}")

        if task_plan:
            plan_text = "\n".join(
                f"{i+1}. {step.get('description', str(step))}"
                for i, step in enumerate(task_plan)
            )
            system_parts.append(f"Execution plan:\n{plan_text}")

        system_content = "\n\n".join(system_parts)

        history = self.compress_conversation(
            conversation_history,
            self.get_available_context(),
        )

        messages: list[dict[str, Any]] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})

        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        return system_content, messages

    def count_tokens_approx(self, text: str) -> int:
        return len(text) // 4


context_manager = ContextManager()
