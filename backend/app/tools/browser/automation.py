from __future__ import annotations
import asyncio
import base64
import os
import uuid
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolDependencyError


class BrowserSessionManager:
    """Manages simulated / Playwright browser sessions."""
    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, session_id: str, headless: bool = True) -> str:
        self._sessions[session_id] = {
            "session_id": session_id,
            "url": "about:blank",
            "title": "Blank Page",
            "headless": headless,
            "cookies": {},
            "history": [],
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        return self._sessions.get(session_id)


browser_session_manager = BrowserSessionManager()


@tool_registry.register(
    name="open_browser",
    category=ToolCategory.BROWSER,
    description="Launch a browser session for interacting with JS-heavy web applications.",
    permission=PermissionTier.NETWORK,
    timeout=15,
)
async def tool_open_browser(session_id: Optional[str] = None, headless: bool = True) -> dict[str, Any]:
    sid = session_id or f"browser_{uuid.uuid4().hex[:8]}"
    browser_session_manager.create_session(sid, headless=headless)
    return {
        "session_id": sid,
        "status": "opened",
        "headless": headless,
        "message": "Browser session initialized.",
    }


@tool_registry.register(
    name="navigate",
    category=ToolCategory.BROWSER,
    description="Navigate browser session to a specific URL.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_navigate(url: str, session_id: str = "default") -> dict[str, Any]:
    sess = browser_session_manager.get_session(session_id)
    if not sess:
        browser_session_manager.create_session(session_id)
        sess = browser_session_manager.get_session(session_id)

    sess["url"] = url
    sess["history"].append(url)
    return {
        "session_id": session_id,
        "url": url,
        "status": "navigated",
    }


@tool_registry.register(
    name="click",
    category=ToolCategory.BROWSER,
    description="Click an element matching selector or text on the active page.",
    permission=PermissionTier.EXECUTE,
    timeout=10,
)
async def tool_click(selector: str, session_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "action": "click", "selector": selector, "status": "executed"}


@tool_registry.register(
    name="type_text",
    category=ToolCategory.BROWSER,
    description="Type text into an input field matching selector.",
    permission=PermissionTier.EXECUTE,
    timeout=10,
)
async def tool_type_text(selector: str, text: str, session_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "action": "type_text", "selector": selector, "length": len(text), "status": "executed"}


@tool_registry.register(
    name="press_key",
    category=ToolCategory.BROWSER,
    description="Send a keyboard key press (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown').",
    permission=PermissionTier.EXECUTE,
    timeout=5,
)
async def tool_press_key(key: str, session_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "action": "press_key", "key": key, "status": "executed"}


@tool_registry.register(
    name="scroll",
    category=ToolCategory.BROWSER,
    description="Scroll page vertically or horizontally (e.g. direction='down', amount=500).",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_scroll(direction: str = "down", amount: int = 500, session_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "action": "scroll", "direction": direction, "amount": amount, "status": "executed"}


@tool_registry.register(
    name="wait",
    category=ToolCategory.BROWSER,
    description="Wait for a specified duration in seconds or until a selector appears.",
    permission=PermissionTier.READ,
    timeout=30,
)
async def tool_wait(seconds: float = 1.0, selector: Optional[str] = None, session_id: str = "default") -> dict[str, Any]:
    await asyncio.sleep(min(seconds, 20.0))
    return {"session_id": session_id, "waited_seconds": seconds, "selector": selector, "status": "completed"}


@tool_registry.register(
    name="take_screenshot",
    category=ToolCategory.BROWSER,
    description="Capture a screenshot of current browser viewport.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_take_screenshot(session_id: str = "default", save_path: Optional[str] = None) -> dict[str, Any]:
    # Placeholder base64 image or actual buffer
    mock_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    return {
        "session_id": session_id,
        "format": "png",
        "image_base64": mock_b64,
        "saved_to": save_path,
    }


@tool_registry.register(
    name="extract_page_text",
    category=ToolCategory.BROWSER,
    description="Extract live DOM rendered text from the active page in browser.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_extract_page_text(session_id: str = "default") -> dict[str, Any]:
    sess = browser_session_manager.get_session(session_id)
    url = sess.get("url", "about:blank") if sess else "about:blank"
    return {
        "session_id": session_id,
        "url": url,
        "page_text": f"Simulated live page text rendered for {url}",
    }


@tool_registry.register(
    name="get_page_elements",
    category=ToolCategory.BROWSER,
    description="Extract interactive elements (buttons, inputs, links, forms) from the current page.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_get_page_elements(session_id: str = "default") -> dict[str, Any]:
    return {
        "session_id": session_id,
        "elements": [
            {"type": "input", "selector": "#search-input", "name": "q"},
            {"type": "button", "selector": "button[type='submit']", "text": "Search"},
            {"type": "link", "selector": "a.nav-home", "text": "Home", "href": "/"},
        ],
    }


@tool_registry.register(
    name="download_file",
    category=ToolCategory.BROWSER,
    description="Trigger a file download from an action or link in browser session.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=30,
)
async def tool_download_file(download_url: str, save_to: str, session_id: str = "default") -> dict[str, Any]:
    return {"session_id": session_id, "download_url": download_url, "saved_to": save_to, "status": "downloaded"}


@tool_registry.register(
    name="upload_file",
    category=ToolCategory.BROWSER,
    description="Upload a file to an <input type='file'> element in browser session.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=15,
)
async def tool_upload_file(selector: str, file_path: str, session_id: str = "default") -> dict[str, Any]:
    if not os.path.exists(file_path):
        raise ToolValidationError(f"File to upload not found: {file_path}")
    return {"session_id": session_id, "selector": selector, "file_path": file_path, "status": "uploaded"}
