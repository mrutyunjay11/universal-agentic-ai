from __future__ import annotations
import logging
import time

from fastapi import APIRouter

from app.models.schemas import SystemInfo
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


@router.get("/system", response_model=SystemInfo)
async def get_system_info():
    info: dict = {
        "uptime_seconds": time.time() - _start_time,
    }

    try:
        import psutil
        info["ram_used"] = psutil.virtual_memory().used
        info["ram_total"] = psutil.virtual_memory().total
        info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        info["ram_used"] = 0
        info["ram_total"] = 0
        info["cpu_percent"] = 0

    try:
        import subprocess
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 3:
                info["gpu_utilization"] = float(parts[0])
                info["gpu_memory_used"] = float(parts[1])
                info["gpu_memory_total"] = float(parts[2])
    except Exception:
        pass

    available = await ollama_client.is_available()
    if available:
        info["model_loaded"] = "ollama_connected"

    return SystemInfo(**info)


@router.get("/system/health")
async def health_check():
    ollama_ok = await ollama_client.is_available()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": "connected" if ollama_ok else "unavailable",
        "uptime_seconds": time.time() - _start_time,
    }
