# =============================================================================
# File: test_cia_thread_controller.py
# Purpose: Verifies CIA thread ownership, overlap prevention, and cleanup.
# =============================================================================

from threading import Event
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QSignalSpy, QTest

from stonks.gui.workers.cia_thread_controller import CiaThreadController


@pytest.fixture
def app() -> QCoreApplication:
    """Provide a Qt event loop for queued worker signals."""
    return QCoreApplication.instance() or QCoreApplication([])


def wait_for_controller_idle(
    controller: CiaThreadController,
    timeout_ms: int = 3000,
) -> bool:
    """Process Qt events until the CIA controller becomes idle."""

    from time import monotonic

    deadline = monotonic() + timeout_ms / 1000.0

    while controller.is_running() and monotonic() < deadline:
        QCoreApplication.processEvents()
        QTest.qWait(10)

    QCoreApplication.processEvents()

    return not controller.is_running()


def test_controller_completes_and_returns_idle(app: QCoreApplication) -> None:
    expected = object()
    service = Mock()
    service.analyze.return_value = expected
    controller = CiaThreadController(lambda: service)
    completed = QSignalSpy(controller.completed)
    idle = QSignalSpy(controller.idle)

    assert controller.start_analysis(" amd ") is True
    assert wait_for_controller_idle(controller)
    assert idle.count() == 1
    assert completed.count() == 1
    assert completed.at(0)[0] is expected
    assert not controller.is_running()
    service.analyze.assert_called_once_with("AMD", limit=50)


def test_controller_rejects_overlapping_requests(app: QCoreApplication) -> None:
    entered = Event()
    release = Event()
    service = Mock()

    def analyze(ticker: str, limit: int = 50) -> object:
        entered.set()
        if not release.wait(3):
            raise TimeoutError("Test service timed out")
        return object()

    service.analyze.side_effect = analyze
    controller = CiaThreadController(lambda: service)
    idle = QSignalSpy(controller.idle)

    try:
        assert controller.start_analysis("AMD") is True
        assert entered.wait(2)
        assert controller.start_analysis("NVDA") is False
    finally:
        release.set()
        assert wait_for_controller_idle(controller)
        assert idle.count() == 1

    assert service.analyze.call_count == 1
    assert not controller.is_running()


def test_controller_validates_before_start(app: QCoreApplication) -> None:
    factory = Mock()
    controller = CiaThreadController(factory)

    with pytest.raises(ValueError):
        controller.start_analysis(" ")
    with pytest.raises(ValueError):
        controller.start_analysis("AMD", limit=0)

    factory.assert_not_called()
    assert not controller.is_running()


def test_controller_reports_failure_and_returns_idle(app: QCoreApplication) -> None:
    service = Mock()
    service.analyze.side_effect = RuntimeError("Provider unavailable")
    controller = CiaThreadController(lambda: service)
    failed = QSignalSpy(controller.failed)
    idle = QSignalSpy(controller.idle)

    assert controller.start_analysis("AMD") is True
    assert wait_for_controller_idle(controller)
    assert idle.count() == 1
    assert failed.count() == 1
    assert failed.at(0)[0] == "Provider unavailable"
    assert not controller.is_running()
