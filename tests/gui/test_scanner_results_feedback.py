# =============================================================================
# File: test_scanner_results_feedback.py
# Purpose: Verify Scanner Workspace displays scan outcomes and market results.
# =============================================================================

from stonks.gui.main_window import MainWindow
from stonks.models.quote_data import QuoteData
from stonks.models.scanner_candidate import ScannerCandidate


def make_candidate(symbol: str = "TEST") -> ScannerCandidate:
    """
    Construct a scanner candidate without requesting market data.

    Args:
        symbol:
            Ticker identifier for the fake candidate.

    Returns:
        ScannerCandidate:
            Candidate containing deterministic quote values.
    """
    quote = QuoteData(
        symbol=symbol,
        price=12.5,
        volume=123456,
        change_percent=3.2,
        gap_percent=-1.1,
        latest_trading_day="2026-10-25",
        relative_volume=2.5,
    )
    return ScannerCandidate(quote_data=quote, float_data=None)


def test_completed_scan_populates_results_and_status(qtbot):
    """Verify completed scans render candidates and a match count."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page

    window.m_scanner_controller.completed.emit([make_candidate("ABCD")])

    assert page.m_results_table.rowCount() == 1
    assert page.m_results_table.item(0, 0).text() == "ABCD"
    assert page.m_results_table.item(0, 1).text() == "$12.50"
    assert page.m_results_table.item(0, 5).text() == "2.50"
    assert page.m_status_label.text() == "Scan complete: 1 match."


def test_zero_matches_clears_old_results(qtbot):
    """Verify a completed empty scan replaces stale prior matches."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page

    window.m_scanner_controller.completed.emit([make_candidate()])
    window.m_scanner_controller.completed.emit([])

    assert page.m_results_table.rowCount() == 0
    assert page.m_status_label.text() == "Scan complete: no matches."


def test_failure_keeps_previous_results(qtbot):
    """Verify an execution failure does not erase last successful results."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page

    window.m_scanner_controller.completed.emit([make_candidate()])
    window.m_scanner_controller.failed.emit("Provider unavailable")

    assert page.m_results_table.rowCount() == 1
    assert page.m_status_label.text() == "Scan failed: Provider unavailable"


def test_cancellation_keeps_previous_results(qtbot):
    """Verify cancellation is distinct from failure and preserves results."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page

    window.m_scanner_controller.completed.emit([make_candidate()])
    window.m_scanner_controller.cancelled.emit()

    assert page.m_results_table.rowCount() == 1
    assert page.m_status_label.text() == "Scan cancelled."


def test_idle_transition_does_not_overwrite_final_status(qtbot):
    """Verify thread cleanup preserves the outcome shown to the user."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_scanner_page

    page.set_running(True)
    window.m_scanner_controller.completed.emit([])
    page.set_running(False)

    assert page.m_status_label.text() == "Scan complete: no matches."
