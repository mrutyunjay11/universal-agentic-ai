from __future__ import annotations
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Callable

from app.config import settings
from app.models.schemas import ToolResult, PermissionTier
from app.services.ollama_client import ollama_client
from app.services.context_manager import context_manager
from app.services.tool_call_parser import parse_tool_call, validate_tool_call, inject_error_context
from app.services.session_manager import session_manager
from app.tools.registry import tool_registry

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class AgentContext:
    goal: str = ""
    plan: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    iteration_count: int = 0
    error_count: int = 0
    error: Optional[str] = None
    start_time: float = 0.0
    pending_approval: Optional[dict] = None
    model: str = settings.primary_model
    project_id: Optional[str] = None
    project_root: str = settings.project_root
    user_message: str = ""
    debug_cycle_count: int = 0


class AgentStateMachine:
    def __init__(self):
        self._state: AgentState = AgentState.IDLE
        self._ctx: AgentContext = AgentContext()
        self._callbacks: dict[str, list[Callable]] = {
            "state_change": [],
            "tool_execution": [],
            "stream": [],
            "approval": [],
            "error": [],
            "done": [],
        }
        self._running = False
        self._permission_granted: PermissionTier = PermissionTier.READ
        self._response_text: str = ""

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def context(self) -> AgentContext:
        return self._ctx

    def on(self, event: str, callback: Callable):
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any = None):
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception as e:
                logger.error("Callback error for %s: %s", event, e)

    def _set_state(self, new_state: AgentState):
        old = self._state
        self._state = new_state
        self._emit("state_change", {"from": old.value, "to": new_state.value})
        logger.info("Agent state: %s -> %s", old.value, new_state.value)

    async def start(
        self,
        user_message: str,
        project_id: Optional[str] = None,
        project_root: str = settings.project_root,
        session_id: Optional[str] = None,
        permission: PermissionTier = PermissionTier.READ,
    ):
        self._ctx = AgentContext(
            goal=user_message,
            user_message=user_message,
            project_id=project_id,
            project_root=project_root,
            start_time=time.time(),
        )
        self._permission_granted = permission
        self._running = True
        self._response_text = ""

        if session_id:
            saved_state = await session_manager.load_agent_state(session_id)
            if saved_state:
                self._ctx.history = saved_state.get("history", [])
                self._ctx.plan = saved_state.get("plan", [])
                self._ctx.current_step = saved_state.get("current_step", 0)

        await self._run_loop(session_id)

    async def _run_loop(self, session_id: Optional[str] = None):
        try:
            task_complexity = await self._analyze_task()

            if task_complexity == "simple":
                await self._execute_simple()
            else:
                await self._plan_and_execute(session_id)
        except asyncio.CancelledError:
            self._set_state(AgentState.CANCELLED)
            self._emit("done", {"state": "cancelled", "response": self._response_text})
        except Exception as e:
            logger.error("Agent loop error: %s", e, exc_info=True)
            self._ctx.error = str(e)
            self._set_state(AgentState.ERROR)
            self._emit("error", {"error": str(e)})
            self._emit("done", {"state": "error", "response": self._response_text})
        finally:
            self._running = False

    async def _analyze_task(self) -> str:
        self._set_state(AgentState.ANALYZING)
        prompt = (
            f"Classify this coding task as 'simple' (single file, one operation), "
            f"'multi_step' (multiple files or steps), or 'ambiguous' (unclear).\n\n"
            f"Task: {self._ctx.goal}\n\n"
            f"Respond with exactly one word: simple, multi_step, or ambiguous."
        )

        try:
            result = await ollama_client.generate(
                model=self._ctx.model,
                prompt=prompt,
                options={"num_predict": 10, "temperature": 0.1},
            )
            response = result.get("response", "").strip().lower()
            if response in ("simple", "multi_step", "ambiguous"):
                return response
            return "multi_step"
        except Exception as e:
            logger.warning("Task analysis failed: %s, defaulting to multi_step", e)
            return "multi_step"

    async def _execute_simple(self):
        self._set_state(AgentState.EXECUTING)
        system_prompt, messages = context_manager.prepare_prompt(
            user_message=self._ctx.goal,
            conversation_history=self._ctx.history,
            tool_schemas=tool_registry.get_schemas(),
        )

        try:
            async for chunk in ollama_client.chat_stream(
                model=self._ctx.model,
                messages=messages,
            ):
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    self._response_text += content
                    self._emit("stream", {"token": content})

                if chunk.get("done", False):
                    break

            self._set_state(AgentState.DONE)
            self._emit("done", {"response": self._response_text})
        except Exception as e:
            self._ctx.error = str(e)
            self._set_state(AgentState.ERROR)
            self._emit("error", {"error": str(e)})

    async def _plan_and_execute(self, session_id: Optional[str] = None):
        self._set_state(AgentState.PLANNING)

        plan_prompt = (
            f"Create a numbered execution plan for this task. "
            f"Each step must specify a tool name from the available tools.\n\n"
            f"Task: {self._ctx.goal}\n\n"
            f"Available tools:\n"
            + "\n".join(
                f"- {s['name']}: {s['description']}"
                for s in tool_registry.get_schemas()
            )
            + "\n\nRespond with a JSON plan: {\"steps\": [{\"tool\": \"...\", \"args\": {...}, \"description\": \"...\"}]}"
        )

        try:
            result = await ollama_client.generate(
                model=self._ctx.model,
                prompt=plan_prompt,
                options={"temperature": 0.1},
            )
            plan_text = result.get("response", "")

            parsed = parse_tool_call(plan_text)
            if parsed.is_tool_call:
                if parsed.tool == "plan" and parsed.args:
                    steps = parsed.args.get("steps", [])
                    self._ctx.plan = steps[:10]
                else:
                    self._ctx.plan = [{"tool": parsed.tool, "args": parsed.args, "description": ""}]
            else:
                try:
                    plan_json = json.loads(plan_text)
                    steps = plan_json.get("steps", []) if isinstance(plan_json, dict) else plan_json
                    self._ctx.plan = steps[:10] if isinstance(steps, list) else []
                except json.JSONDecodeError:
                    self._ctx.plan = []
        except Exception as e:
            logger.warning("Planning failed: %s", e)
            self._ctx.plan = []

        if not self._ctx.plan:
            self._ctx.plan = [
                {"tool": "read_file", "args": {"file_path": "", "project_root": self._ctx.project_root}, "description": "Read relevant files"},
                {"tool": "execute_terminal", "args": {"session_id": session_id or "default", "command": "ls", "project_root": self._ctx.project_root}, "description": "Explore project structure"},
            ]

        self._emit("stream", {"plan": self._ctx.plan})

        for step_idx, step in enumerate(self._ctx.plan):
            if not self._running:
                break
            if self._ctx.iteration_count >= settings.max_iterations_per_task:
                self._ctx.error = "Max iterations reached"
                self._set_state(AgentState.DONE)
                break
            if time.time() - self._ctx.start_time > settings.max_autonomous_runtime_seconds:
                self._ctx.error = "Max runtime exceeded"
                self._set_state(AgentState.DONE)
                break

            self._ctx.current_step = step_idx
            self._set_state(AgentState.EXECUTING)

            tool_name = step.get("tool", "")
            tool_args = step.get("args", {})
            tool_args.setdefault("project_root", self._ctx.project_root)

            if session_id and "session_id" not in tool_args:
                tool_args["session_id"] = session_id

            tool = tool_registry.get(tool_name)
            if not tool:
                logger.warning("Unknown tool in plan step %d: %s", step_idx, tool_name)
                continue

            if tool.permission == PermissionTier.SYSTEM:
                self._set_state(AgentState.AWAITING_APPROVAL)
                approval_data = {
                    "tool": tool_name,
                    "args": tool_args,
                    "description": step.get("description", ""),
                    "step": step_idx,
                }
                self._ctx.pending_approval = approval_data
                self._emit("approval", approval_data)
                return

            result = await tool_registry.execute_with_retry(
                tool_name=tool_name,
                args=tool_args,
                permission_granted=self._permission_granted,
            )

            self._ctx.tool_results.append(result)
            self._ctx.iteration_count += 1
            self._emit("tool_execution", result)

            if not result.success:
                self._ctx.error_count += 1
                error_context = inject_error_context(
                    tool_name, tool_args, result.error or "Unknown error",
                    self._ctx.error_count, settings.max_retries_per_tool,
                )
                self._ctx.history.append({"role": "system", "content": error_context})

                if self._ctx.error_count >= settings.max_retries_per_tool * 3:
                    self._ctx.error = f"Too many errors: {result.error}"
                    self._set_state(AgentState.ERROR)
                    break

            self._set_state(AgentState.OBSERVING)

        if self._state == AgentState.EXECUTING:
            self._set_state(AgentState.REFLECTING)
            reflect_prompt = (
                f"Original task: {self._ctx.goal}\n\n"
                f"Completed steps: {len(self._ctx.tool_results)}\n"
                f"Successful: {sum(1 for r in self._ctx.tool_results if r.success)}\n"
                f"Failed: {sum(1 for r in self._ctx.tool_results if not r.success)}\n\n"
                f"Is the task complete? Summarize what was done."
            )
            try:
                reflection = await ollama_client.generate(
                    model=self._ctx.model,
                    prompt=reflect_prompt,
                    options={"temperature": 0.3},
                )
                self._response_text = reflection.get("response", "Task completed.")
            except Exception:
                self._response_text = f"Completed {len(self._ctx.tool_results)} tool calls. See tool log for details."

            self._set_state(AgentState.DONE)
            self._emit("done", {"response": self._response_text})

    async def approve_action(self, approved: bool, reason: Optional[str] = None):
        if self._state != AgentState.AWAITING_APPROVAL or not self._ctx.pending_approval:
            return

        approval_data = self._ctx.pending_approval
        self._ctx.pending_approval = None

        if approved:
            tool_name = approval_data["tool"]
            tool_args = approval_data["args"]
            self._set_state(AgentState.EXECUTING)
            result = await tool_registry.execute(
                tool_name=tool_name,
                args=tool_args,
                permission_granted=PermissionTier.SYSTEM,
            )
            self._ctx.tool_results.append(result)
            self._emit("tool_execution", result)
            self._set_state(AgentState.PLANNING)
        else:
            self._ctx.history.append({
                "role": "system",
                "content": f"User rejected: {approval_data['description']}. Reason: {reason or 'No reason given'}",
            })
            self._set_state(AgentState.PLANNING)

    def cancel(self):
        self._running = False
        self._set_state(AgentState.CANCELLED)
        self._emit("done", {"state": "cancelled"})

    async def save_state(self, session_id: str):
        state_data = {
            "state": self._state.value,
            "goal": self._ctx.goal,
            "plan": self._ctx.plan,
            "current_step": self._ctx.current_step,
            "history": self._ctx.history,
            "iteration_count": self._ctx.iteration_count,
            "tool_results": [
                {
                    "tool": r.tool,
                    "success": r.success,
                    "output": str(r.output)[:200] if r.output else None,
                    "error": r.error,
                }
                for r in self._ctx.tool_results
            ],
        }
        await session_manager.save_agent_state(session_id, state_data)


agent_machine = AgentStateMachine()
