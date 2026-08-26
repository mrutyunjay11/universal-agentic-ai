from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.tools.permissions import PermissionTier


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str]
    permission: PermissionTier
    timeout: int = 30


class ToolCall(BaseModel):
    tool: str
    args: dict[str, Any]


class ToolResult(BaseModel):
    tool: str
    args: dict[str, Any]
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: int = 0
    permission: PermissionTier = PermissionTier.READ


class ChatMessage(BaseModel):
    role: str
    content: str
    tool_calls: Optional[list[ToolCall]] = None
    tool_result: Optional[ToolResult] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    message: str
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    message: str
    tool_calls: Optional[list[ToolCall]] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    project_id: Optional[str] = None
    message_count: int
    token_count: int


class ProjectInfo(BaseModel):
    project_id: str
    name: str
    root_path: str
    language: Optional[str] = None
    framework: Optional[str] = None
    indexed: bool = False
    file_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FileInfo(BaseModel):
    path: str
    name: str
    type: str
    size: int
    modified: datetime
    language: Optional[str] = None


class SearchRequest(BaseModel):
    project_id: str
    query: str
    limit: int = 10
    file_pattern: Optional[str] = None


class SearchResult(BaseModel):
    file_path: str
    content: str
    score: float
    chunk_type: str
    line_start: int
    line_end: int


class IndexStatus(BaseModel):
    project_id: str
    status: str
    files_indexed: int
    chunks_indexed: int
    last_indexed: Optional[datetime] = None
    in_progress: bool = False


class SystemInfo(BaseModel):
    model_config = {"protected_namespaces": ()}
    gpu_utilization: Optional[float] = None
    gpu_memory_used: Optional[float] = None
    gpu_memory_total: Optional[float] = None
    ram_used: float
    ram_total: float
    cpu_percent: float
    model_loaded: Optional[str] = None
    uptime_seconds: float


class AgentStateData(BaseModel):
    state: str
    goal: str
    plan: list[dict[str, Any]]
    current_step: int
    history: list[dict[str, Any]]
    iteration_count: int
    tool_results: list[ToolResult]
    error: Optional[str] = None


class ApprovalRequest(BaseModel):
    action_id: str
    tool: str
    args: dict[str, Any]
    description: str
    permission: PermissionTier


class ApprovalResponse(BaseModel):
    action_id: str
    approved: bool
    reason: Optional[str] = None


class WsMessage(BaseModel):
    type: str
    data: dict[str, Any]


def generate_session_id() -> str:
    return str(uuid.uuid4())


def generate_project_id() -> str:
    return str(uuid.uuid4())
