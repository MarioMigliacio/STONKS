# =============================================================================
# File: test_scanner_workspace_integration.py
# Purpose: Verify Scanner Workspace signals control real background execution.
# =============================================================================

from threading import Event

from PySide6.QtCore import QThread

from stonks.gui.main_window import MainWindow
from stonks.models.quote_data import QuoteData
from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_strategy import ScannerStrategy


class FakeScannerStrategy(ScannerStrategy):
    """
    Produce a predictable scanner result without contacting market APIs.

    Attributes:
        strategy_id:
            Stable identifier used by the scanner coordinator.

        display_name:
            Human-readable strategy label.

        m_cancel_event:
            Event shared with the controller for cancellation.
    """

    strategy_id = "existing_scanner"
    display_name = "Fake Scanner"

    def __init__(self, cancel_event: Event) -> None:
        """
        Initialize the fake strategy.

        Args:
            cancel_event:
                Controller-owned cooperative cancellation event.
        """
        self.m_cancel_event = cancel_event

    def scan(self):
        """
        Produce one candidate on the worker thread.

        Returns:
            A list containing one fake scanner candidate.
        """
        assert QThread.currentThread() is not None
        quote = QuoteData(
            symbol="TEST",
            price=12.5,
            volume=100000,
            change_percent=3.0,
            gap_percent=1.0,
            latest_trading_day="2026-10-25",
        )
        return [ScannerCandidate(quote_data=quote, float_data=None)]


class WaitingScannerStrategy(ScannerStrategy):
    """
    Wait until cancellation is requested without making API calls.

    Attributes:
        strategy_id:
            Stable identifier used by the scanner coordinator.

        display_name:
            Human-readable strategy label.

        m_cancel_event:
            Event shared with the controller for cancellation.
    """

    strategy_id = "existing_scanner"
    display_name = "Waiting Scanner"

    def __init__(self, cancel_event: Event) -> None:
        """
        Initialize a cancellable fake strategy.

        Args:
            cancel_event:
                Controller-owned cancellation event.
        """
        self.m_cancel_event = cancel_event

    def scan(self):
        """
        Wait briefly for cancellation and return no results.

        Returns:
            Empty list after cancellation is requested.
        """
        self.m_cancel_event.wait(2)
        return []


def test_run_button_starts_worker_and_restores_controls(qtbot, monkeypatch):
    """Verify Run invokes the controller and returns to idle after completion."""
    import stonks.gui.main_window as main_window_module

    monkeypatch.setattr(
        main_window_module,
        "ExistingScannerStrategy",
        FakeScannerStrategy,
    )
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page
    page.m_strategy_checkboxes["existing_scanner"].setChecked(True)

    try:
        with qtbot.waitSignal(window.m_scanner_controller.idle, timeout=5000):
            page.m_run_button.click()

        assert not window.m_scanner_controller.is_running()
        assert page.m_run_button.isEnabled()
        assert not page.m_cancel_button.isEnabled()
    finally:
        if window.m_scanner_controller.is_running():
            window.m_scanner_controller.request_cancel()
            qtbot.waitUntil(
                lambda: not window.m_scanner_controller.is_running(),
                timeout=5000,
            )


def test_cancel_button_requests_cooperative_shutdown(qtbot, monkeypatch):
    """Verify Cancel signals the active scan and restores idle controls."""
    import stonks.gui.main_window as main_window_module

    monkeypatch.setattr(
        main_window_module,
        "ExistingScannerStrategy",
        WaitingScannerStrategy,
    )
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page
    page.m_strategy_checkboxes["existing_scanner"].setChecked(True)

    try:
        with qtbot.waitSignal(window.m_scanner_controller.idle, timeout=5000):
            page.m_run_button.click()
            assert page.m_cancel_button.isEnabled()
            page.m_cancel_button.click()

        assert not window.m_scanner_controller.is_running()
        assert not page.m_cancel_button.isEnabled()
        assert page.m_run_button.isEnabled()
    finally:
        if window.m_scanner_controller.is_running():
            window.m_scanner_controller.request_cancel()
            qtbot.waitUntil(
                lambda: not window.m_scanner_controller.is_running(),
                timeout=5000,
            )
