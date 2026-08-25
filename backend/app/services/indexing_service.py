from __future__ import annotations
import asyncio
import hashlib
import logging
import os
from typing import Any, Optional

from app.config import settings
from app.services.memory_service import memory_service
from app.services.file_service import compute_file_hash

logger = logging.getLogger(__name__)

try:
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning("tree-sitter not installed. AST-aware chunking disabled.")


LANGUAGE_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".php": "php",
    ".rb": "ruby",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
}

MAX_CHUNK_SIZE = 512


class IndexingService:
    def __init__(self):
        self._parser: Optional[Parser] = None
        self._running = False
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

    async def initialize(self):
        if HAS_TREE_SITTER:
            try:
                self._parser = Parser()
                logger.info("Tree-sitter parser initialized")
            except Exception as e:
                logger.warning("Tree-sitter init failed: %s", e)
                self._parser = None

        self._running = True
        self._worker_task = asyncio.create_task(self._index_worker())

    async def shutdown(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def index_project(
        self,
        project_id: str,
        project_root: str,
        incremental: bool = True,
    ) -> dict[str, Any]:
        chunks: list[dict[str, Any]] = []
        files_indexed = 0
        errors: list[str] = []

        for root, dirs, files in os.walk(project_root):
            dirs[:] = self._skip_dirs(dirs)

            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                language = LANGUAGE_EXTENSIONS.get(ext)
                if not language:
                    continue

                current_hash = compute_file_hash(file_path)

                if incremental:
                    stored_hash = memory_service.get_file_hash(project_id, file_path)
                    if stored_hash == current_hash:
                        continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except (OSError, IOError) as e:
                    errors.append(f"Cannot read {file_path}: {e}")
                    continue

                file_chunks = self._chunk_content(
                    content=content,
                    file_path=file_path,
                    language=language,
                )
                chunks.extend(file_chunks)
                files_indexed += 1
                memory_service.update_file_hash(project_id, file_path, current_hash)

        if chunks:
            await memory_service.index_chunks(project_id, chunks)

        result = {
            "project_id": project_id,
            "files_indexed": files_indexed,
            "chunks_indexed": len(chunks),
            "errors": errors,
        }
        logger.info("Indexed project %s: %d files, %d chunks", project_id, files_indexed, len(chunks))
        return result

    def _skip_dirs(self, dirs: list[str]):
        return [d for d in dirs if d.startswith(".")
                or d == "node_modules"
                or d == "__pycache__"
                or d == ".git"
                or d == "venv"
                or d == ".venv"
                or d == "target"
                or d == "build"
                or d == "dist"]

    def _chunk_content(
        self,
        content: str,
        file_path: str,
        language: str,
    ) -> list[dict[str, Any]]:
        lines = content.split("\n")
        total_lines = len(lines)

        if total_lines <= MAX_CHUNK_SIZE:
            return [
                {
                    "file_path": file_path,
                    "language": language,
                    "chunk_type": "module",
                    "line_start": 1,
                    "line_end": total_lines,
                    "content": content,
                }
            ]

        chunks: list[dict[str, Any]] = []
        if self._parser and HAS_TREE_SITTER:
            ast_chunks = self._ast_chunk(content, file_path, language, lines)
            if ast_chunks:
                chunks = ast_chunks

        if not chunks:
            chunks = self._line_chunk(content, file_path, language, lines)

        return chunks

    def _line_chunk(
        self,
        content: str,
        file_path: str,
        language: str,
        lines: list[str],
        chunk_size: int = MAX_CHUNK_SIZE,
    ) -> list[dict]:
        chunks = []
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i : i + chunk_size]
            chunks.append(
                {
                    "file_path": file_path,
                    "language": language,
                    "chunk_type": "code",
                    "line_start": i + 1,
                    "line_end": min(i + len(chunk_lines), len(lines)),
                    "content": "\n".join(chunk_lines),
                }
            )
        return chunks

    def _ast_chunk(
        self,
        content: str,
        file_path: str,
        language: str,
        lines: list[str],
    ) -> list[dict]:
        chunks = []
        current_class: Optional[str] = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            if language == "python":
                if stripped.startswith(("def ", "async def ")):
                    chunk_type = "method" if current_class else "function"
                    content_lines = self._extend_to_next_top_level(lines, i)
                    chunks.append(
                        {
                            "file_path": file_path,
                            "language": language,
                            "chunk_type": chunk_type,
                            "line_start": i + 1,
                            "line_end": i + len(content_lines),
                            "content": "\n".join(content_lines),
                        }
                    )
                elif stripped.startswith("class "):
                    current_class = stripped
                    content_lines = self._extend_to_next_top_level(lines, i)
                    chunks.append(
                        {
                            "file_path": file_path,
                            "language": language,
                            "chunk_type": "class",
                            "line_start": i + 1,
                            "line_end": i + len(content_lines),
                            "content": "\n".join(content_lines),
                        }
                    )

            elif language in ("javascript", "typescript", "tsx", "jsx"):
                if stripped.startswith(("function ", "async function ", "const ", "let ", "var ")):
                    if "=>" in stripped or "=" in stripped:
                        continue
                    content_lines = self._extend_ts_function(lines, i)
                    chunks.append(
                        {
                            "file_path": file_path,
                            "language": language,
                            "chunk_type": "function",
                            "line_start": i + 1,
                            "line_end": i + len(content_lines),
                            "content": "\n".join(content_lines),
                        }
                    )
                elif stripped.startswith(("class ", "interface ", "type ")):
                    content_lines = self._extend_ts_block(lines, i)
                    chunks.append(
                        {
                            "file_path": file_path,
                            "language": language,
                            "chunk_type": "class",
                            "line_start": i + 1,
                            "line_end": i + len(content_lines),
                            "content": "\n".join(content_lines),
                        }
                    )

        if not chunks:
            chunks = self._line_chunk(content, file_path, language, lines)

        return chunks

    def _extend_to_next_top_level(self, lines: list[str], start: int) -> list[str]:
        result: list[str] = []
        indent = None
        for i in range(start, len(lines)):
            line = lines[i]
            if indent is None and line.strip() and not line.strip().startswith("#"):
                indent = len(line) - len(line.lstrip())
            result.append(line)
            if i > start and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                if len(line) - len(line.lstrip()) <= (indent or 0):
                    if not line.strip().startswith(("def ", "class ", "async ", "@", "#")):
                        result.pop()
                        break
            if i > start and line.strip() == "" and result:
                pass
        return result

    def _extend_ts_function(self, lines: list[str], start: int) -> list[str]:
        return self._extend_ts_block(lines, start)

    def _extend_ts_block(self, lines: list[str], start: int) -> list[str]:
        result: list[str] = []
        brace_count = 0
        found_open = False
        for i in range(start, len(lines)):
            line = lines[i]
            result.append(line)
            for ch in line:
                if ch == "{":
                    brace_count += 1
                    found_open = True
                elif ch == "}":
                    brace_count -= 1
            if found_open and brace_count == 0:
                break
        return result

    async def queue_index(self, project_id: str, project_root: str, incremental: bool = True):
        await self._queue.put({
            "project_id": project_id,
            "project_root": project_root,
            "incremental": incremental,
        })

    async def _index_worker(self):
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=2.0)
                await self.index_project(
                    project_id=task["project_id"],
                    project_root=task["project_root"],
                    incremental=task.get("incremental", True),
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Index worker error: %s", e)

    async def watch_project(self, project_id: str, project_root: str):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class IndexHandler(FileSystemEventHandler):
                def __init__(self, svc, pid, proot):
                    self.svc = svc
                    self.pid = pid
                    self.proot = proot

                def on_modified(self, event):
                    if not event.is_directory:
                        asyncio.create_task(
                            self.svc.queue_index(self.pid, self.proot, incremental=True)
                        )

            event_handler = IndexHandler(self, project_id, project_root)
            observer = Observer()
            observer.schedule(event_handler, project_root, recursive=True)
            observer.start()
            logger.info("File watcher started for %s", project_root)
        except ImportError:
            logger.warning("watchdog not installed. File watching disabled.")


indexing_service = IndexingService()
