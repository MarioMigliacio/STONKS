# =============================================================================
# File: test_research_main_window_integration.py
# Purpose: Verifies MainWindow research dispatch and safe worker shutdown.
# =============================================================================

from datetime import date
from threading import Event

from PySide6.QtCore import QThread

from stonks.gui.main_window import MainWindow
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.research_interval import ResearchInterval


def _request():
    return HistoricalResearchRequest(
        symbol="AMD",
        start_date=date(2026, 10, 30),
        end_date=date(2026, 10, 30),
        interval=ResearchInterval.ONE_MINUTE,
    )


def _result(request):
    return HistoricalResearchResult(
        request=request,
        source_candles=[],
        display_candles=[],
        window_metrics=None,
        data_source=ResearchDataSource.CACHE,
        status=ResearchDataStatus.AVAILABLE,
    )


def test_research_request_reaches_worker_and_updates_page(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    main_thread = QThread.currentThread()
    calls = []

    def runner(request):
        assert QThread.currentThread() != main_thread
        calls.append(request)
        return _result(request)

    window.m_research_controller.m_runner = runner
    window.m_research_page.show_loading()

    with qtbot.waitSignal(window.m_research_controller.idle, timeout=5000):
        window.m_research_page.research_requested.emit(_request())

    assert len(calls) == 1
    assert window.m_research_page.m_presentation_state == "available"
    assert "Source: cache" in window.m_research_page.m_metrics_message.text()
    assert not window.m_research_controller.is_running()


def test_research_failure_releases_page(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    def runner(request):
        raise RuntimeError("Synthetic research failure")

    window.m_research_controller.m_runner = runner
    window.m_research_page.show_loading()

    with qtbot.waitSignal(window.m_research_controller.idle, timeout=5000):
        window.m_research_page.research_requested.emit(_request())

    assert window.m_research_page.m_presentation_state == "error"
    assert "Synthetic research failure" in window.m_research_page.m_chart_message.text()
    assert not window.m_research_page.m_running


def test_close_waits_for_research_worker(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    entered = Event()
    release = Event()

    def runner(request):
        entered.set()
        if not release.wait(3):
            raise TimeoutError("Test runner timed out")
        return _result(request)

    window.m_research_controller.m_runner = runner

    try:
        assert window.m_research_controller.start_research(_request())
        assert entered.wait(2)
        window.close()
        assert window.isVisible()
        assert window.m_close_pending
    finally:
        release.set()

    with qtbot.waitSignal(window.m_research_controller.idle, timeout=5000):
        pass
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=3000)
    assert not window.m_close_pending
