# =============================================================================
# File: test_scanner_worker_cancellation.py
# Purpose: Verifies worker cancellation signals and lifecycle completion.
# =============================================================================

from threading import Event
from unittest.mock import Mock

from PySide6.QtTest import QSignalSpy

from stonks.gui.workers.scanner_worker import ScannerWorker


def test_worker_emits_cancelled_when_requested():
    """Verify pre-cancellation emits cancelled and finished, but not success."""
    event = Event()
    event.set()

    coordinator = Mock()
    worker = ScannerWorker(coordinator, event)

    completed_spy = QSignalSpy(worker.completed)
    failed_spy = QSignalSpy(worker.failed)
    cancelled_spy = QSignalSpy(worker.cancelled)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    coordinator.scan.assert_not_called()
    assert completed_spy.count() == 0
    assert failed_spy.count() == 0
    assert cancelled_spy.count() == 1
    assert finished_spy.count() == 1
