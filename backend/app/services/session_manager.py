from __future__ import annotations
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)


class Session:
    def __init__(
        self,
        session_id: str,
        project_id: Optional[str] = None,
    ):
        self.session_id = session_id
        self.project_id = project_id
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at
        self.messages: list[dict[str, Any]] = []
        self.token_count: int = 0
        self.metadata: dict[str, Any] = {}

    def add_message(self, message: dict[str, Any], token_count: int = 0):
        self.messages.append(message)
        self.token_count += token_count
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
            "token_count": self.token_count,
            "metadata": self.metadata,
        }


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._db: Optional[aiosqlite.Connection] = None
        self._lock: Any = None

    async def initialize(self):
        self._db = await aiosqlite.connect(settings.sqlite_path)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                project_id TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                tool_calls TEXT,
                tool_result TEXT,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS edit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                file_path TEXT,
                original_content TEXT,
                patch TEXT,
                applied_at TEXT,
                success INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                session_id TEXT PRIMARY KEY,
                state_data TEXT,
                updated_at TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        await self._db.commit()

    async def shutdown(self):
        if self._db:
            await self._db.close()

    def create_session(self, project_id: Optional[str] = None) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id, project_id=project_id)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[list[dict]] = None,
        tool_result: Optional[dict] = None,
    ):
        if not self._db:
            return
        session = self.get_session(session_id)
        if not session:
            return

        timestamp = datetime.utcnow().isoformat()
        await self._db.execute(
            """INSERT INTO messages (session_id, role, content, tool_calls, tool_result, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                json.dumps(tool_result) if tool_result else None,
                timestamp,
            ),
        )
        await self._db.execute(
            """UPDATE sessions SET updated_at = ?, message_count = message_count + 1
               WHERE session_id = ?""",
            (timestamp, session_id),
        )
        await self._db.commit()

    async def save_agent_state(self, session_id: str, state_data: dict):
        if not self._db:
            return
        await self._db.execute(
            """INSERT OR REPLACE INTO agent_states (session_id, state_data, updated_at)
               VALUES (?, ?, ?)""",
            (session_id, json.dumps(state_data), datetime.utcnow().isoformat()),
        )
        await self._db.commit()

    async def load_agent_state(self, session_id: str) -> Optional[dict]:
        if not self._db:
            return None
        cursor = await self._db.execute(
            "SELECT state_data FROM agent_states WHERE session_id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    async def get_session_history(self, session_id: str, limit: int = 50) -> list[dict]:
        if not self._db:
            return []
        cursor = await self._db.execute(
            """SELECT role, content, tool_calls, tool_result, timestamp
               FROM messages WHERE session_id = ?
               ORDER BY id DESC LIMIT ?""",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        messages = []
        for row in reversed(rows):
            msg = {
                "role": row[0],
                "content": row[1],
                "timestamp": row[4],
            }
            if row[2]:
                msg["tool_calls"] = json.loads(row[2])
            if row[3]:
                msg["tool_result"] = json.loads(row[3])
            messages.append(msg)
        return messages


session_manager = SessionManager()
