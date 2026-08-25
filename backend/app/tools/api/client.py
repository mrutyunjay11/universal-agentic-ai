from __future__ import annotations
import json
import urllib.parse
from typing import Any, Optional
import httpx

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.tools.audit import redact_secrets
from app.tools.provenance import create_provenance, SourceType


def _sanitize_headers(headers: Optional[dict[str, str]]) -> dict[str, str]:
    if not headers:
        return {}
    return {k: v for k, v in headers.items()}


@tool_registry.register(
    name="http_get",
    category=ToolCategory.API,
    description="Make a secure HTTP GET request to a REST API endpoint and return JSON/text.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_http_get(
    url: str,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, Any]] = None,
    timeout: int = 15,
) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ToolValidationError(f"Invalid URL schema: {url}")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
        except Exception as e:
            raise ToolValidationError(f"HTTP GET failed: {e}")

    is_json = "application/json" in resp.headers.get("content-type", "")
    body_data = resp.json() if is_json else resp.text[:10000]

    prov = create_provenance(
        source_type=SourceType.API_RESPONSE,
        uri=url,
        content=resp.text[:5000],
        title=f"API GET {urllib.parse.urlparse(url).path}",
        extraction_method="rest_api_client",
    )

    return {
        "url": url,
        "status_code": resp.status_code,
        "is_json": is_json,
        "data": redact_secrets(body_data),
        "_provenance": prov,
    }


@tool_registry.register(
    name="http_post",
    category=ToolCategory.API,
    description="Send an HTTP POST request with JSON payload to an API endpoint.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=20,
)
async def tool_http_post(
    url: str,
    json_body: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 15,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, json=json_body, headers=headers)
        except Exception as e:
            raise ToolValidationError(f"HTTP POST failed: {e}")

    is_json = "application/json" in resp.headers.get("content-type", "")
    return {
        "url": url,
        "status_code": resp.status_code,
        "data": redact_secrets(resp.json() if is_json else resp.text[:5000]),
    }


@tool_registry.register(
    name="http_put",
    category=ToolCategory.API,
    description="Send an HTTP PUT request with payload.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=20,
)
async def tool_http_put(url: str, json_body: Optional[dict[str, Any]] = None, headers: Optional[dict[str, str]] = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.put(url, json=json_body, headers=headers)
    return {"url": url, "status_code": resp.status_code, "data": redact_secrets(resp.text[:5000])}


@tool_registry.register(
    name="http_patch",
    category=ToolCategory.API,
    description="Send an HTTP PATCH request to update resource attributes.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=20,
)
async def tool_http_patch(url: str, json_body: Optional[dict[str, Any]] = None, headers: Optional[dict[str, str]] = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.patch(url, json=json_body, headers=headers)
    return {"url": url, "status_code": resp.status_code, "data": redact_secrets(resp.text[:5000])}


@tool_registry.register(
    name="http_delete",
    category=ToolCategory.API,
    description="Send an HTTP DELETE request to remove an external resource (gated by DESTRUCTIVE tier).",
    permission=PermissionTier.DESTRUCTIVE,
    timeout=20,
)
async def tool_http_delete(url: str, headers: Optional[dict[str, str]] = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.delete(url, headers=headers)
    return {"url": url, "status_code": resp.status_code, "data": redact_secrets(resp.text[:5000])}


@tool_registry.register(
    name="graphql_query",
    category=ToolCategory.API,
    description="Execute a GraphQL query or mutation against a GraphQL endpoint.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_graphql_query(
    endpoint: str,
    query: str,
    variables: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    payload = {"query": query, "variables": variables or {}}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(endpoint, json=payload, headers=headers)
    return {"endpoint": endpoint, "status_code": resp.status_code, "response": redact_secrets(resp.json())}


@tool_registry.register(
    name="inspect_api",
    category=ToolCategory.API,
    description="Inspect an OpenAPI / Swagger definition or GraphQL schema for available routes and models.",
    permission=PermissionTier.NETWORK,
    timeout=15,
)
async def tool_inspect_api(spec_url_or_path: str) -> dict[str, Any]:
    if spec_url_or_path.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(spec_url_or_path)
            data = resp.json()
    else:
        with open(spec_url_or_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    paths = list(data.get("paths", {}).keys()) if isinstance(data, dict) else []
    return {
        "title": data.get("info", {}).get("title", "API Spec"),
        "version": data.get("info", {}).get("version", "1.0"),
        "endpoints_count": len(paths),
        "sample_endpoints": paths[:20],
    }


@tool_registry.register(
    name="validate_response",
    category=ToolCategory.API,
    description="Validate an API JSON response structure against an expected JSON schema.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_validate_response(response_data: dict[str, Any], required_keys: list[str]) -> dict[str, Any]:
    missing = [k for k in required_keys if k not in response_data]
    return {
        "valid": len(missing) == 0,
        "missing_keys": missing,
        "present_keys": list(response_data.keys()),
    }
