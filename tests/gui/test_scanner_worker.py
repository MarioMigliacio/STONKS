# =============================================================================
# File: test_scanner_worker.py
# Purpose: Tests scanner worker success, failure, and completion signals.
# =============================================================================

from unittest.mock import Mock

from PySide6.QtTest import QSignalSpy

from stonks.gui.workers.scanner_worker import ScannerWorker


def test_worker_emits_results_on_success():
    """Verify successful scans emit candidates and finish."""
    candidates = [object(), object()]

    coordinator = Mock()
    coordinator.scan.return_value = candidates

    worker = ScannerWorker(coordinator)

    completed_spy = QSignalSpy(worker.completed)
    failed_spy = QSignalSpy(worker.failed)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    coordinator.scan.assert_called_once_with()

    assert completed_spy.count() == 1
    assert completed_spy.at(0)[0] == candidates

    assert failed_spy.count() == 0
    assert finished_spy.count() == 1


def test_worker_emits_failure_and_finishes():
    """Verify scanner exceptions emit failure and cleanup signals."""
    coordinator = Mock()
    coordinator.scan.side_effect = RuntimeError("API unavailable")

    worker = ScannerWorker(coordinator)

    completed_spy = QSignalSpy(worker.completed)
    failed_spy = QSignalSpy(worker.failed)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    coordinator.scan.assert_called_once_with()

    assert completed_spy.count() == 0
    assert failed_spy.count() == 1
    assert failed_spy.at(0)[0] == "API unavailable"
    assert finished_spy.count() == 1


def test_worker_emits_finished_after_empty_results():
    """Verify an empty successful scan still emits completion."""
    coordinator = Mock()
    coordinator.scan.return_value = []

    worker = ScannerWorker(coordinator)

    completed_spy = QSignalSpy(worker.completed)
    finished_spy = QSignalSpy(worker.finished)

    worker.run()

    assert completed_spy.count() == 1
    assert completed_spy.at(0)[0] == []
    assert finished_spy.count() == 1
