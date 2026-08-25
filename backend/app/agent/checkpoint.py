from __future__ import annotations
import os
import json
import uuid
import datetime
from typing import Optional
from app.agent.state import AgentState


class CheckpointManager:
    """Saves and restores task state checkpoints for pause/resume and fault recovery."""

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self._in_memory: dict[str, list[dict]] = {}
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def save_checkpoint(self, state: AgentState) -> str:
        cp_id = f"cp_{uuid.uuid4().hex[:8]}_{int(datetime.datetime.now().timestamp())}"
        state.checkpoints.append(cp_id)

        state_data = state.model_dump()

        # In-memory save
        if state.task_id not in self._in_memory:
            self._in_memory[state.task_id] = []
        self._in_memory[state.task_id].append(state_data)

        # File save
        file_path = os.path.join(self.checkpoint_dir, f"{state.task_id}_{cp_id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)
        except Exception:
            pass

        return cp_id

    def load_latest_checkpoint(self, task_id: str) -> Optional[AgentState]:
        # Try memory first
        if task_id in self._in_memory and self._in_memory[task_id]:
            latest = self._in_memory[task_id][-1]
            return AgentState(**latest)

        # Try disk
        try:
            files = [f for f in os.listdir(self.checkpoint_dir) if f.startswith(f"{task_id}_") and f.endswith(".json")]
            if files:
                files.sort()
                latest_file = os.path.join(self.checkpoint_dir, files[-1])
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return AgentState(**data)
        except Exception:
            pass

        return None

    def list_checkpoints(self, task_id: str) -> list[str]:
        if task_id in self._in_memory:
            return [d.get("checkpoints", [""])[-1] for d in self._in_memory[task_id] if d.get("checkpoints")]
        return []


checkpoint_manager = CheckpointManager()
