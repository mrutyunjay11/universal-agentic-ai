from __future__ import annotations
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class GPUDevice(BaseModel):
    device_id: str
    name: str = "NVIDIA A100-SXM4-80GB"
    total_vram_mb: int = 81920
    allocated_vram_mb: int = 0
    exclusive_task_id: Optional[str] = None


class GPUScheduler:
    """
    Schedules GPU-intensive tasks (multimodal, vision, fine-tuning, large model inference).
    Manages VRAM allocation, exclusive vs shared workloads, and priority scheduling.
    """

    def __init__(self):
        self._devices: dict[str, GPUDevice] = {
            "gpu-0": GPUDevice(device_id="gpu-0"),
            "gpu-1": GPUDevice(device_id="gpu-1"),
        }

    def allocate_gpu(
        self,
        task_id: str,
        required_vram_mb: int = 8192,
        exclusive: bool = False,
    ) -> Optional[str]:
        for dev in self._devices.values():
            if dev.exclusive_task_id is not None:
                continue

            if exclusive:
                if dev.allocated_vram_mb == 0:
                    dev.exclusive_task_id = task_id
                    dev.allocated_vram_mb = dev.total_vram_mb
                    return dev.device_id
            else:
                available = dev.total_vram_mb - dev.allocated_vram_mb
                if available >= required_vram_mb:
                    dev.allocated_vram_mb += required_vram_mb
                    return dev.device_id

        return None

    def release_gpu(self, device_id: str, released_vram_mb: int = 8192, task_id: Optional[str] = None) -> bool:
        dev = self._devices.get(device_id)
        if not dev:
            return False

        if dev.exclusive_task_id == task_id or dev.exclusive_task_id is not None:
            dev.exclusive_task_id = None
            dev.allocated_vram_mb = 0
        else:
            dev.allocated_vram_mb = max(0, dev.allocated_vram_mb - released_vram_mb)

        return True

    def get_gpu_status(self) -> list[dict[str, Any]]:
        return [dev.model_dump() for dev in self._devices.values()]


gpu_scheduler = GPUScheduler()
