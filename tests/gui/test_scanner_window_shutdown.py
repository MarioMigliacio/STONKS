# =============================================================================
# File: test_scanner_window_shutdown.py
# Purpose: Verifies safe MainWindow closure during active scanner execution.
# =============================================================================

from threading import Event

from stonks.gui.main_window import MainWindow
from stonks.scanner.scanner_strategy import ScannerStrategy


class WaitingStrategy(ScannerStrategy):
    """
    Simulate a running scanner that acknowledges cooperative cancellation.

    Attributes:
        strategy_id:
            Stable identifier for the test strategy.

        display_name:
            Human-readable name for the test strategy.

        started:
            Event set when background execution begins.

        cancel_event:
            Shared cancellation event supplied by the controller.
    """

    strategy_id = "waiting"
    display_name = "Waiting Strategy"

    def __init__(self, started: Event, cancel_event: Event) -> None:
        """
        Initialize a controllable test strategy.

        Args:
            started: Event signalling that the scan has started.
            cancel_event: Event used to request cancellation.
        """
        self.started = started
        self.cancel_event = cancel_event

    def scan(self) -> list:
        """
        Wait for cancellation and return no results.

        Returns:
            An empty list after cancellation is requested.
        """
        self.started.set()
        if not self.cancel_event.wait(timeout=5):
            raise RuntimeError("Timed out waiting for test cancellation")
        return []


def test_main_window_closes_when_idle(qtbot):
    """Verify the existing idle close behavior remains unchanged."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.close()
    assert not window.isVisible()


def test_close_during_scan_waits_for_idle(qtbot):
    """Verify close is deferred until the running scanner thread stops."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    started = Event()
    controller = window.m_scanner_controller
    assert controller.start_scan([lambda event: WaitingStrategy(started, event)])

    # The wait is bounded; if the test fails, request cancellation in finally.
    try:
        qtbot.waitUntil(started.is_set, timeout=3000)
        assert controller.is_running()

        assert not window.close()
        assert window.isVisible()
        assert window.m_close_pending

        qtbot.waitUntil(lambda: not controller.is_running(), timeout=6000)
        qtbot.waitUntil(lambda: not window.isVisible(), timeout=3000)
        assert not window.m_close_pending
    finally:
        controller.request_cancel()
        if controller.is_running():
            qtbot.waitUntil(lambda: not controller.is_running(), timeout=6000)


def test_close_while_cancellation_pending(qtbot):
    """Verify repeated close requests do not destroy the active thread."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    started = Event()
    controller = window.m_scanner_controller
    assert controller.start_scan([lambda event: WaitingStrategy(started, event)])

    try:
        qtbot.waitUntil(started.is_set, timeout=3000)
        assert not window.close()
        # A second close must be ignored while the controller owns a thread.
        if controller.is_running():
            assert not window.close()
            assert window.isVisible()

        qtbot.waitUntil(lambda: not controller.is_running(), timeout=6000)
        qtbot.waitUntil(lambda: not window.isVisible(), timeout=3000)
    finally:
        controller.request_cancel()
        if controller.is_running():
            qtbot.waitUntil(lambda: not controller.is_running(), timeout=6000)
