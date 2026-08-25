from __future__ import annotations
import pytest
from app.services.tool_call_parser import (
    parse_tool_call,
    ToolCallParseResult,
    validate_tool_call,
    inject_error_context,
)


class TestToolCallParser:
    def test_strict_json_parse(self):
        result = parse_tool_call('{"tool": "read_file", "args": {"file_path": "test.py"}}')
        assert result.is_tool_call
        assert result.tool == "read_file"
        assert result.args == {"file_path": "test.py"}
        assert result.parse_method == "strict_json"

    def test_strict_json_with_function_key(self):
        result = parse_tool_call('{"function": "write_file", "params": {"file_path": "test.py", "content": "hello"}}')
        assert result.is_tool_call
        assert result.tool == "write_file"
        assert "file_path" in result.args
        assert result.parse_method == "strict_json"

    def test_regex_balanced_braces(self):
        text = 'I think we should use the tool: {"tool": "list_directory", "args": {"dir_path": "."}}'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "list_directory"
        assert result.args == {"dir_path": "."}
        assert result.parse_method == "regex_braces"

    def test_regex_braces_with_extra_text(self):
        text = 'Let me check the file.\n```json\n{"tool": "read_file", "args": {"file_path": "main.py"}}\n```\nDone.'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "read_file"
        assert result.args == {"file_path": "main.py"}

    def test_fuzzy_extract_tool_name(self):
        text = 'I will use the tool: read_file with file_path = "test.py"'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "read_file"
        assert result.parse_method in ("fuzzy_name_only", "fuzzy_json", "fuzzy_args", "regex_pattern")

    def test_fuzzy_extract_with_args(self):
        text = 'tool = "execute_terminal", args = {"command": "ls -la"}'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "execute_terminal"
        assert result.parse_method in ("fuzzy_args", "fuzzy_json", "regex_pattern")

    def test_plain_text_no_tool_call(self):
        result = parse_tool_call("Hello, how can I help you today?")
        assert not result.is_tool_call
        assert result.text == "Hello, how can I help you today?"
        assert result.parse_method == "plain_text"

    def test_empty_input(self):
        result = parse_tool_call("")
        assert not result.is_tool_call
        assert result.error == "Empty output"

    def test_whitespace_input(self):
        result = parse_tool_call("   \n  ")
        assert not result.is_tool_call

    def test_malformed_json_strict(self):
        result = parse_tool_call('{"tool": "read_file" "args": {}}')
        assert result.parse_method != "strict_json"

    def test_tool_name_in_backticks(self):
        result = parse_tool_call('Use `read_file` to read the file')
        assert result.is_tool_call
        assert result.tool == "read_file"

    def test_nested_braces(self):
        json_str = '{"tool": "execute_terminal", "args": {"command": "echo {\"nested\": true}"}}'
        result = parse_tool_call(json_str)
        assert result.is_tool_call
        assert result.tool == "execute_terminal"

    def test_args_as_string(self):
        result = parse_tool_call('{"tool": "write_file", "args": "{\\"file_path\\": \\"test.py\\", \\"content\\": \\"hi\\"}"}')
        assert result.is_tool_call
        assert result.tool == "write_file"
        assert isinstance(result.args, dict)

    def test_code_block_json(self):
        text = "Here's what I'll do:\n```\n{\n  \"tool\": \"git_status\",\n  \"args\": {}\n}\n```"
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "git_status"


class TestToolCallValidation:
    def test_valid_tool(self):
        result = ToolCallParseResult(tool="read_file", args={}, is_tool_call=True)
        error = validate_tool_call(result, {"read_file", "write_file"})
        assert error == ""

    def test_unknown_tool(self):
        result = ToolCallParseResult(tool="nonexistent_tool", args={}, is_tool_call=True)
        error = validate_tool_call(result, {"read_file", "write_file"})
        assert "Unknown tool" in error

    def test_empty_tool_name(self):
        result = ToolCallParseResult(tool="", args={}, is_tool_call=True)
        error = validate_tool_call(result, {"read_file"})
        assert "empty" in error.lower()

    def test_not_a_tool_call(self):
        result = ToolCallParseResult(text="hello", is_tool_call=False)
        error = validate_tool_call(result, {"read_file"})
        assert error == ""


class TestErrorContext:
    def test_error_context_format(self):
        context = inject_error_context(
            tool_name="read_file",
            args={"file_path": "test.py"},
            error_message="File not found",
            retry_count=1,
            max_retries=3,
        )
        assert "read_file" in context
        assert "File not found" in context
        assert "attempt 1/3" in context
        assert "file_path" in context

    def test_error_context_retry_count(self):
        context = inject_error_context(
            tool_name="execute_terminal",
            args={"command": "ls"},
            error_message="Timeout",
            retry_count=3,
            max_retries=3,
        )
        assert "attempt 3/3" in context
        assert "Timeout" in context


class TestEdgeCases:
    def test_unicode_in_tool_name(self):
        result = parse_tool_call('{"tool": "read_file", "args": {"path": "/tmp/测试.py"}}')
        assert result.is_tool_call
        assert result.tool == "read_file"

    def test_very_long_args(self):
        long_arg = "a" * 10000
        text = f'{{"tool": "write_file", "args": {{"file_path": "test.txt", "content": "{long_arg}"}}}}'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "write_file"

    def test_multiple_json_blocks(self):
        text = 'First: {"tool": "read_file", "args": {"file_path": "a.py"}} Then: {"tool": "write_file", "args": {"file_path": "b.py"}}'
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "read_file"

    def test_single_quotes(self):
        result = parse_tool_call("{'tool': 'read_file', 'args': {'file_path': 'test.py'}}")
        assert result.is_tool_call
        assert result.tool == "read_file"

    def test_newlines_in_json(self):
        text = """{
            "tool": "execute_terminal",
            "args": {
                "command": "ls -la"
            }
        }"""
        result = parse_tool_call(text)
        assert result.is_tool_call
        assert result.tool == "execute_terminal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
