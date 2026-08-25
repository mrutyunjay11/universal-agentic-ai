import pytest
import time
from app.autonomy.watchdog import Watchdog
from app.autonomy.task_graph import TaskGraph, SubTask


class TestWatchdog:
    def test_stall_detection(self):
        wd = Watchdog(stall_timeout_seconds=0.1)
        wd.record_progress()
        assert wd.check_for_stalls() is False

        time.sleep(0.15)
        assert wd.check_for_stalls() is True

        wd.record_progress()
        assert wd.check_for_stalls() is False
