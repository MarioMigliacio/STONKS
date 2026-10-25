# =============================================================================
# File: test_scanner_thread_controller.py
# Purpose: Tests scanner QThread execution, cancellation, and cleanup.
# =============================================================================

from threading import Event

from PySide6.QtCore import QThread

from stonks.gui.workers.scanner_thread_controller import ScannerThreadController
from stonks.scanner.scanner_cancelled import ScannerCancelled
from stonks.scanner.scanner_strategy import ScannerStrategy


class ControlledStrategy(ScannerStrategy):
    """
    Simulate scanning without external API calls.

    Attributes:
        strategy_id:
            Unique strategy identifier.

        display_name:
            Human-readable strategy name.

        m_event:
            Event shared with the worker and coordinator.

        m_started:
            Event indicating that scanning has begun.

        m_mode:
            Behavior selected for the test.

        m_main_thread:
            Main Qt thread for thread-affinity verification.
    """

    strategy_id = "controlled"
    display_name = "Controlled Scanner"

    def __init__(self, event: Event, started: Event, mode: str, main_thread: QThread) -> None:
        """Initialize the fake strategy with synchronization events."""
        self.m_event = event
        self.m_started = started
        self.m_mode = mode
        self.m_main_thread = main_thread

    def scan(self) -> list:
        """Execute the requested test scenario on the worker thread."""
        assert QThread.currentThread() != self.m_main_thread
        self.m_started.set()
        if self.m_mode == "error":
            raise RuntimeError("Synthetic scanner failure")
        if self.m_mode == "wait":
            self.m_event.wait(3)
            if self.m_event.is_set():
                raise ScannerCancelled("Scanner execution cancelled.")
        return []


def test_scan_completes_and_thread_cleans_up(qtbot):
    """Verify normal completion releases the thread before becoming idle."""
    controller = ScannerThreadController()
    started = Event()
    results = []
    controller.completed.connect(results.append)

    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_scan(
            [lambda event: ControlledStrategy(event, started, "success", QThread.currentThread())]
        )

    assert started.is_set()
    assert results == [[]]
    assert not controller.is_running()


def test_failure_still_cleans_up(qtbot):
    """Verify a failing strategy reports an error and stops its thread."""
    controller = ScannerThreadController()
    errors = []
    controller.failed.connect(errors.append)

    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_scan(
            [lambda event: ControlledStrategy(event, Event(), "error", QThread.currentThread())]
        )

    assert errors == ["Synthetic scanner failure"]
    assert not controller.is_running()


def test_duplicate_launch_rejected_and_cancellation_acknowledged(qtbot):
    """Verify only one active scan and cooperative cancellation."""
    controller = ScannerThreadController()
    started = Event()
    cancellations = []
    controller.cancelled.connect(lambda: cancellations.append(True))

    with qtbot.waitSignal(controller.idle, timeout=5000):
        assert controller.start_scan(
            [lambda event: ControlledStrategy(event, started, "wait", QThread.currentThread())]
        )
        assert not controller.start_scan(
            [lambda event: ControlledStrategy(event, Event(), "success", QThread.currentThread())]
        )
        assert controller.request_cancel()

    assert cancellations == [True]
    assert not controller.is_running()
    assert not controller.request_cancel()
