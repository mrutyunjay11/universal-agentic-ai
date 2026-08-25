from __future__ import annotations
import json
import re
from typing import Any, Optional


class ToolCallParseResult:
    def __init__(
        self,
        tool: Optional[str] = None,
        args: Optional[dict[str, Any]] = None,
        text: Optional[str] = None,
        is_tool_call: bool = False,
        error: Optional[str] = None,
        parse_method: str = "none",
    ):
        self.tool = tool
        self.args = args or {}
        self.text = text
        self.is_tool_call = is_tool_call
        self.error = error
        self.parse_method = parse_method

    def __repr__(self) -> str:
        if self.is_tool_call:
            return f"ToolCallParseResult(tool={self.tool!r}, args={self.args!r}, method={self.parse_method})"
        return f"ToolCallParseResult(text={self.text!r}, method={self.parse_method})"


def _find_balanced_braces(text: str) -> Optional[str]:
    stack = []
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append(i)
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start >= 0:
                    return text[start : i + 1]
    return None


def _normalize_keys(d: dict[str, Any]) -> dict[str, Any]:
    key_map = {
        "tool_name": "tool",
        "function": "tool",
        "action": "tool",
        "name": "tool",
        "params": "args",
        "parameters": "args",
        "kwargs": "args",
        "arguments": "args",
    }
    normalized: dict[str, Any] = {}
    for k, v in d.items():
        k_lower = k.lower().strip()
        target = key_map.get(k_lower, k_lower)
        normalized[target] = v
    return normalized


def _fuzzy_extract(text: str) -> Optional[ToolCallParseResult]:
    tool_match = re.search(
        r'(?:tool|function|action)\s*[=:"]\s*["\']?(\w+)["\']?',
        text,
        re.IGNORECASE,
    )
    if not tool_match:
        return None
    tool_name = tool_match.group(1)

    args_start = text.find("{", tool_match.end())
    if args_start >= 0:
        args_json = _find_balanced_braces(text[args_start:])
        if args_json:
            try:
                args = json.loads(args_json)
                return ToolCallParseResult(
                    tool=tool_name,
                    args=args if isinstance(args, dict) else {"value": args},
                    is_tool_call=True,
                    parse_method="fuzzy_json",
                )
            except json.JSONDecodeError:
                pass

    args_match = re.search(
        r'(?:args|params|kwargs|arguments|with)\s*[=:]\s*(\{.*?\})',
        text[tool_match.end():],
        re.DOTALL,
    )
    if args_match:
        try:
            args = json.loads(args_match.group(1))
            return ToolCallParseResult(
                tool=tool_name,
                args=args if isinstance(args, dict) else {"value": args},
                is_tool_call=True,
                parse_method="fuzzy_args",
            )
        except json.JSONDecodeError:
            pass

    return ToolCallParseResult(
        tool=tool_name,
        args={},
        is_tool_call=True,
        parse_method="fuzzy_name_only",
    )


def parse_tool_call(model_output: str) -> ToolCallParseResult:
    if not model_output or not model_output.strip():
        return ToolCallParseResult(
            text="", is_tool_call=False, error="Empty output", parse_method="none"
        )

    text = model_output.strip()

    # Try 1: Strict JSON parse
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                normalized = _normalize_keys(parsed)
                tool = normalized.get("tool", "")
                if tool:
                    args = normalized.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {"value": args}
                    return ToolCallParseResult(
                        tool=tool,
                        args=args if isinstance(args, dict) else {"value": args},
                        is_tool_call=True,
                        parse_method="strict_json",
                    )
        except json.JSONDecodeError:
            pass

    # Try 2: Extract JSON block with balanced braces
    json_block = _find_balanced_braces(text)
    if json_block:
        try:
            parsed = json.loads(json_block)
            if isinstance(parsed, dict):
                normalized = _normalize_keys(parsed)
                tool = normalized.get("tool", "")
                if tool:
                    args = normalized.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except json.JSONDecodeError:
                            args = {"value": args}
                    return ToolCallParseResult(
                        tool=tool,
                        args=args if isinstance(args, dict) else {"value": args},
                        is_tool_call=True,
                        parse_method="regex_braces",
                    )
        except json.JSONDecodeError:
            pass

    # Try 3: Fuzzy key matching
    fuzzy_result = _fuzzy_extract(text)
    if fuzzy_result:
        return fuzzy_result

    # Try 4: Look for simple JSON-like patterns with tool/args or backtick tool
    tool_patterns = [
        r'"tool"\s*:\s*"(\w+)"',
        r"'tool'\s*:\s*'(\w+)'",
        r"tool\s*=\s*[\"']?(\w+)[\"']?",
        r"(?:Use|call|run|using)\s+`([a-zA-Z0-9_]+)`",
    ]
    for pattern in tool_patterns:
        m = re.search(pattern, text)
        if m:
            tool_name = m.group(1)
            return ToolCallParseResult(
                tool=tool_name,
                args={},
                is_tool_call=True,
                parse_method="regex_pattern",
            )

    # Not a tool call — classify as plain text
    return ToolCallParseResult(
        text=text, is_tool_call=False, parse_method="plain_text"
    )


def inject_error_context(
    tool_name: str, args: dict, error_message: str, retry_count: int, max_retries: int
) -> str:
    return (
        f"Tool execution failed (attempt {retry_count}/{max_retries}).\n"
        f"Tool: {tool_name}\n"
        f"Arguments: {json.dumps(args, indent=2)}\n"
        f"Error: {error_message}\n\n"
        f"Please analyze the error and either:\n"
        f"1. Fix the arguments and retry the same tool\n"
        f"2. Use a different approach with a different tool\n"
        f"3. If this is unrecoverable, explain the issue to the user"
    )


def validate_tool_call(result: ToolCallParseResult, available_tools: set[str]) -> str:
    if not result.is_tool_call:
        return ""
    if not result.tool:
        return "Tool name is empty"
    if result.tool not in available_tools:
        return f"Unknown tool: {result.tool}. Available: {sorted(available_tools)}"
    return ""
