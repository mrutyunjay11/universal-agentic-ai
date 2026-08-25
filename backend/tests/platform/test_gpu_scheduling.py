import pytest
from app.platform.gpu_scheduler import GPUScheduler


class TestGPUScheduler:
    def test_gpu_shared_and_exclusive_allocation(self):
        scheduler = GPUScheduler()

        # Shared allocation
        dev_id = scheduler.allocate_gpu("task_vision_01", required_vram_mb=16384, exclusive=False)
        assert dev_id is not None
        assert dev_id.startswith("gpu-")

        # Exclusive allocation
        exclusive_dev = scheduler.allocate_gpu("task_training_02", exclusive=True)
        assert exclusive_dev is not None
        assert exclusive_dev != dev_id

        # Release
        assert scheduler.release_gpu(dev_id, released_vram_mb=16384) is True
        assert scheduler.release_gpu(exclusive_dev, task_id="task_training_02") is True
