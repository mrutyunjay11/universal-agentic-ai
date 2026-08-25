from __future__ import annotations
import asyncio
import logging
import os
import signal
from typing import Optional

from app.utils.security import validate_command, enforce_project_root
from app.config import settings

logger = logging.getLogger(__name__)


class TerminalError(Exception):
    pass


class TerminalSession:
    def __init__(self, session_id: str, project_root: str):
        self.session_id = session_id
        self.project_root = project_root
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._output_queue: asyncio.Queue[str] = asyncio.Queue()

    async def execute(self, command: str, timeout: int = 30) -> list[str]:
        validation = validate_command(command)
        if not validation["allowed"]:
            raise TerminalError(validation["reason"] or "Command not allowed")

        abs_root = enforce_project_root(self.project_root, self.project_root)
        if not abs_root:
            raise TerminalError(f"Invalid project root: {self.project_root}")

        output_lines: list[str] = []

        try:
            self._process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=abs_root,
                env={
                    **os.environ,
                    "DEBIAN_FRONTEND": "noninteractive",
                },
            )
            self._running = True
        except Exception as e:
            raise TerminalError(f"Failed to start process: {e}")

        try:
            async with asyncio.timeout(timeout):
                while True:
                    line = await self._process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").rstrip("\n")
                    output_lines.append(decoded)
                    await self._output_queue.put(decoded)

                await self._process.wait()
        except asyncio.TimeoutError:
            self._kill()
            raise TerminalError(
                f"Command timed out after {timeout}s: {command[:100]}"
            )
        except Exception as e:
            self._kill()
            raise TerminalError(f"Command execution error: {e}")
        finally:
            self._running = False

        return output_lines

    async def stream_output(self) -> asyncio.Queue[str]:
        return self._output_queue

    def _kill(self):
        if self._process and self._process.returncode is None:
            try:
                self._process.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass

    @property
    def running(self) -> bool:
        return self._running

    @property
    def return_code(self) -> Optional[int]:
        return self._process.returncode if self._process else None

    def close(self):
        self._kill()


class TerminalManager:
    def __init__(self):
        self._sessions: dict[str, TerminalSession] = {}

    def create_session(self, session_id: str, project_root: str) -> TerminalSession:
        session = TerminalSession(
            session_id=session_id,
            project_root=project_root,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        return self._sessions.get(session_id)

    def close_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()

    async def close_all(self):
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()


terminal_manager = TerminalManager()
