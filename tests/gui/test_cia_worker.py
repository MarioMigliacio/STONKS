# =============================================================================
# File: test_cia_worker.py
# Purpose: Verifies CIA worker success, failure, and finalization signals.
# =============================================================================

from unittest.mock import Mock

from stonks.gui.workers.cia_worker import CiaWorker


def test_worker_emits_result_and_finishes() -> None:
    expected = object()
    service = Mock()
    service.analyze.return_value = expected
    worker = CiaWorker(service, "AMD", 3)
    results = []
    errors = []
    finished = []
    worker.completed.connect(results.append)
    worker.failed.connect(errors.append)
    worker.finished.connect(lambda: finished.append(True))

    worker.run()

    service.analyze.assert_called_once_with("AMD", limit=3)
    assert results == [expected]
    assert errors == []
    assert finished == [True]


def test_worker_emits_failure_and_finishes() -> None:
    service = Mock()
    service.analyze.side_effect = RuntimeError("Provider unavailable")
    worker = CiaWorker(service, "AMD")
    results = []
    errors = []
    finished = []
    worker.completed.connect(results.append)
    worker.failed.connect(errors.append)
    worker.finished.connect(lambda: finished.append(True))

    worker.run()

    assert results == []
    assert errors == ["Provider unavailable"]
    assert finished == [True]
