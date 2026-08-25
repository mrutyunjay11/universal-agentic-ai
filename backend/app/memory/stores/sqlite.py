from __future__ import annotations
import asyncio
import json
import sqlite3
import os
from typing import Any, Optional
from app.memory.base import MemoryStore
from app.memory.models import MemoryRecord, MemoryType, MemoryScope, VerificationStatus, FreshnessStatus


class SQLiteMemoryStore(MemoryStore):
    """
    High-performance SQLite metadata and keyword memory storage backend.
    Enforces indexing, thread-safe asynchronous execution, and JSON metadata serialization.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._init_db_sync)

    def _init_db_sync(self) -> None:
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_records (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    source TEXT,
                    source_ids TEXT,
                    task_id TEXT,
                    session_id TEXT,
                    project_id TEXT,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    confidence REAL DEFAULT 0.8,
                    importance REAL DEFAULT 0.5,
                    relevance REAL DEFAULT 0.5,
                    verification_status TEXT DEFAULT 'UNVERIFIED',
                    freshness_status TEXT DEFAULT 'CURRENT',
                    expires_at TEXT,
                    superseded_by TEXT,
                    version INTEGER DEFAULT 1,
                    tags TEXT,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memory_records(memory_type)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_scope ON memory_records(scope)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_proj ON memory_records(project_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_user ON memory_records(user_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_fresh ON memory_records(freshness_status)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_ver ON memory_records(verification_status)")

    async def insert(self, record: MemoryRecord) -> MemoryRecord:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _insert_sync():
                with self._conn:
                    self._conn.execute("""
                        INSERT INTO memory_records (
                            id, memory_type, scope, content, summary, source, source_ids,
                            task_id, session_id, project_id, user_id, created_at, updated_at,
                            last_accessed_at, access_count, confidence, importance, relevance,
                            verification_status, freshness_status, expires_at, superseded_by,
                            version, tags, metadata, embedding
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.id, record.memory_type.value, record.scope.value, record.content, record.summary,
                        record.source, json.dumps(record.source_ids), record.task_id, record.session_id,
                        record.project_id, record.user_id, record.created_at, record.updated_at,
                        record.last_accessed_at, record.access_count, record.confidence, record.importance,
                        record.relevance, record.verification_status.value, record.freshness_status.value,
                        record.expires_at, record.superseded_by, record.version, json.dumps(record.tags),
                        json.dumps(record.metadata), json.dumps(record.embedding) if record.embedding else None,
                    ))
                return record

            return await asyncio.to_thread(_insert_sync)

    async def get(self, memory_id: str) -> Optional[MemoryRecord]:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _get_sync():
                cursor = self._conn.cursor()
                cursor.execute("SELECT * FROM memory_records WHERE id = ?", (memory_id,))
                row = cursor.fetchone()
                return self._row_to_record(row) if row else None

            return await asyncio.to_thread(_get_sync)

    async def update(self, record: MemoryRecord) -> MemoryRecord:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _update_sync():
                with self._conn:
                    self._conn.execute("""
                        UPDATE memory_records SET
                            memory_type = ?, scope = ?, content = ?, summary = ?, source = ?,
                            source_ids = ?, task_id = ?, session_id = ?, project_id = ?,
                            user_id = ?, created_at = ?, updated_at = ?, last_accessed_at = ?,
                            access_count = ?, confidence = ?, importance = ?, relevance = ?,
                            verification_status = ?, freshness_status = ?, expires_at = ?,
                            superseded_by = ?, version = ?, tags = ?, metadata = ?, embedding = ?
                        WHERE id = ?
                    """, (
                        record.memory_type.value, record.scope.value, record.content, record.summary,
                        record.source, json.dumps(record.source_ids), record.task_id, record.session_id,
                        record.project_id, record.user_id, record.created_at, record.updated_at,
                        record.last_accessed_at, record.access_count, record.confidence, record.importance,
                        record.relevance, record.verification_status.value, record.freshness_status.value,
                        record.expires_at, record.superseded_by, record.version, json.dumps(record.tags),
                        json.dumps(record.metadata), json.dumps(record.embedding) if record.embedding else None,
                        record.id,
                    ))
                return record

            return await asyncio.to_thread(_update_sync)

    async def delete(self, memory_id: str) -> bool:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _delete_sync():
                with self._conn:
                    cursor = self._conn.execute("DELETE FROM memory_records WHERE id = ?", (memory_id,))
                    return cursor.rowcount > 0

            return await asyncio.to_thread(_delete_sync)

    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        scope: Optional[MemoryScope] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        min_confidence: float = 0.0,
        include_stale: bool = False,
    ) -> list[MemoryRecord]:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _search_sync():
                clauses = ["confidence >= ?"]
                params: list[Any] = [min_confidence]

                if not include_stale:
                    clauses.append("freshness_status IN ('CURRENT', 'UNKNOWN')")

                if memory_type:
                    clauses.append("memory_type = ?")
                    params.append(memory_type.value)

                if scope:
                    clauses.append("scope = ?")
                    params.append(scope.value)

                if project_id:
                    clauses.append("(project_id = ? OR scope = 'GLOBAL')")
                    params.append(project_id)

                if user_id:
                    clauses.append("(user_id = ? OR user_id IS NULL)")
                    params.append(user_id)

                if task_id:
                    clauses.append("task_id = ?")
                    params.append(task_id)

                if query.strip():
                    clauses.append("(content LIKE ? OR summary LIKE ? OR tags LIKE ?)")
                    term = f"%{query.strip()}%"
                    params.extend([term, term, term])

                sql = f"SELECT * FROM memory_records WHERE {' AND '.join(clauses)} ORDER BY importance DESC, created_at DESC LIMIT ?"
                params.append(limit)

                cursor = self._conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [self._row_to_record(r) for r in rows]

            return await asyncio.to_thread(_search_sync)

    async def list_all(
        self,
        limit: int = 100,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[MemoryRecord]:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _list_sync():
                clauses = ["1=1"]
                params: list[Any] = []
                if memory_type:
                    clauses.append("memory_type = ?")
                    params.append(memory_type.value)
                if project_id:
                    clauses.append("project_id = ?")
                    params.append(project_id)
                if user_id:
                    clauses.append("user_id = ?")
                    params.append(user_id)

                sql = f"SELECT * FROM memory_records WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                cursor = self._conn.cursor()
                cursor.execute(sql, params)
                return [self._row_to_record(r) for r in cursor.fetchall()]

            return await asyncio.to_thread(_list_sync)

    async def count(
        self,
        memory_type: Optional[MemoryType] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _count_sync():
                clauses = ["1=1"]
                params: list[Any] = []
                if memory_type:
                    clauses.append("memory_type = ?")
                    params.append(memory_type.value)
                if project_id:
                    clauses.append("project_id = ?")
                    params.append(project_id)
                if user_id:
                    clauses.append("user_id = ?")
                    params.append(user_id)

                sql = f"SELECT COUNT(*) as c FROM memory_records WHERE {' AND '.join(clauses)}"
                cursor = self._conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                return int(row["c"]) if row else 0

            return await asyncio.to_thread(_count_sync)

    async def clear(self) -> None:
        if self._conn is None:
            await self.initialize()

        async with self._lock:
            def _clear_sync():
                with self._conn:
                    self._conn.execute("DELETE FROM memory_records")

            await asyncio.to_thread(_clear_sync)

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        embedding_val = json.loads(row["embedding"]) if row["embedding"] else None
        return MemoryRecord(
            id=row["id"],
            memory_type=MemoryType(row["memory_type"]),
            scope=MemoryScope(row["scope"]),
            content=row["content"],
            summary=row["summary"],
            source=row["source"],
            source_ids=json.loads(row["source_ids"]) if row["source_ids"] else [],
            task_id=row["task_id"],
            session_id=row["session_id"],
            project_id=row["project_id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_accessed_at=row["last_accessed_at"],
            access_count=row["access_count"],
            confidence=row["confidence"],
            importance=row["importance"],
            relevance=row["relevance"],
            verification_status=VerificationStatus(row["verification_status"]),
            freshness_status=FreshnessStatus(row["freshness_status"]),
            expires_at=row["expires_at"],
            superseded_by=row["superseded_by"],
            version=row["version"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            embedding=embedding_val,
        )
