from __future__ import annotations
import time
from typing import Any, Optional
from pydantic import BaseModel, Field


class ScalingDecision(BaseModel):
    action: str  # "SCALE_UP", "SCALE_DOWN", "NOOP"
    pool_type: str
    current_workers: int
    target_workers: int
    reason: str
    timestamp: float = Field(default_factory=time.time)


class Autoscaler:
    """
    Dynamic autoscaling engine.
    Calculates scale-up and scale-down decisions based on queue depth, worker utilization,
    latency, and cooldown hysteresis to prevent rapid oscillation.
    """

    def __init__(
        self,
        min_workers: int = 1,
        max_workers: int = 20,
        cooldown_seconds: float = 10.0,
        tasks_per_worker_target: int = 3,
    ):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.cooldown = cooldown_seconds
        self.tasks_per_worker = tasks_per_worker_target
        self._last_scale_time: dict[str, float] = {}

    def evaluate_scaling(
        self,
        pool_type: str,
        current_workers: int,
        queue_depth: int,
        avg_worker_utilization_pct: float = 50.0,
    ) -> ScalingDecision:
        now = time.time()
        last_scale = self._last_scale_time.get(pool_type, 0.0)

        if now - last_scale < self.cooldown:
            return ScalingDecision(
                action="NOOP",
                pool_type=pool_type,
                current_workers=current_workers,
                target_workers=current_workers,
                reason="In cooldown period",
            )

        # Scale up logic
        if queue_depth > current_workers * self.tasks_per_worker or avg_worker_utilization_pct > 80.0:
            target = min(self.max_workers, max(current_workers + 2, (queue_depth // self.tasks_per_worker) + 1))
            if target > current_workers:
                self._last_scale_time[pool_type] = now
                return ScalingDecision(
                    action="SCALE_UP",
                    pool_type=pool_type,
                    current_workers=current_workers,
                    target_workers=target,
                    reason=f"High load: queue_depth={queue_depth}, utilization={avg_worker_utilization_pct:.1f}%",
                )

        # Scale down logic
        if queue_depth == 0 and avg_worker_utilization_pct < 20.0 and current_workers > self.min_workers:
            target = max(self.min_workers, current_workers - 1)
            if target < current_workers:
                self._last_scale_time[pool_type] = now
                return ScalingDecision(
                    action="SCALE_DOWN",
                    pool_type=pool_type,
                    current_workers=current_workers,
                    target_workers=target,
                    reason="Low load: idle queue and low utilization",
                )

        return ScalingDecision(
            action="NOOP",
            pool_type=pool_type,
            current_workers=current_workers,
            target_workers=current_workers,
            reason="Workload balanced",
        )


autoscaler = Autoscaler()
