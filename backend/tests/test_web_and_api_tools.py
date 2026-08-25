from __future__ import annotations
import pytest
from app.tools.registry import tool_registry
from app.tools.base import ToolContext
from app.tools.permissions import PermissionTier


@pytest.mark.asyncio
class TestWebAndApiTools:
    async def test_extract_web_content_clean_markdown(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Documentation Page</title></head>
        <body>
            <header><p>Header to ignore</p></header>
            <h1>Introduction to Universal Agents</h1>
            <p>Universal agents execute <code>tools</code> reliably.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <a href="https://example.com/docs">Documentation Link</a>
        </body>
        </html>
        """
        res = await tool_registry.execute("extract_web_content", {"html_content": sample_html}, ctx)
        assert res.success
        assert res.output["title"] == "Test Documentation Page"
        assert "Introduction to Universal Agents" in res.output["content"]
        assert "`tools`" in res.output["content"]
        assert res.output["content_hash"] is not None

    async def test_validate_response_schema(self):
        ctx = ToolContext(permission_granted=PermissionTier.READ)
        mock_api_data = {"status": "ok", "user_id": 123, "token": "xyz"}
        res = await tool_registry.execute("validate_response", {
            "response_data": mock_api_data,
            "required_keys": ["status", "user_id"],
        }, ctx)
        assert res.success
        assert res.output["valid"] is True
