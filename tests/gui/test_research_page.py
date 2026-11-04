# =============================================================================
# File: test_research_page.py
# Purpose: Verifies research controls, validation, and request signals.
# =============================================================================

import pytest
from PySide6.QtCore import QDate
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from stonks.gui.pages.research_page import ResearchPage
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.market_session import MarketSession
from stonks.models.research_interval import ResearchInterval


@pytest.fixture
def page():
    """Construct a standalone research page for widget tests."""
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    widget = ResearchPage()
    yield widget
    widget.close()


def test_initial_controls_and_interval_options(page):
    assert page.m_interval_combo.count() == len(ResearchInterval)
    assert page.m_interval_combo.currentData() == ResearchInterval.ONE_MINUTE
    assert not page.m_end_date.isEnabled()
    assert page.m_session_combo.isEnabled()
    assert page.m_session_combo.currentData() is None


def test_intraday_date_tracks_start_date(page):
    chosen = QDate(2026, 10, 30)
    page.m_start_date.setDate(chosen)
    assert page.m_end_date.date() == chosen


def test_daily_interval_enables_date_range_and_resets_session(page):
    page.m_session_combo.setCurrentIndex(2)
    page.m_interval_combo.setCurrentIndex(6)
    assert page.m_interval_combo.currentData() == ResearchInterval.DAILY
    assert page.m_end_date.isEnabled()
    assert not page.m_session_combo.isEnabled()
    assert page.m_session_combo.currentData() is None


def test_analyze_emits_validated_cached_request(page):
    page.m_ticker_input.setText("  nvda  ")
    page.m_start_date.setDate(QDate(2026, 10, 30))
    page.m_session_combo.setCurrentIndex(2)
    spy = QSignalSpy(page.research_requested)

    page.m_analyze_button.click()

    assert spy.count() == 1
    request = spy.at(0)[0]
    assert isinstance(request, HistoricalResearchRequest)
    assert request.symbol == "NVDA"
    assert request.start_date == request.end_date
    assert request.session == MarketSession.REGULAR
    assert request.interval == ResearchInterval.ONE_MINUTE
    assert request.force_refresh is False


def test_refresh_sets_force_refresh(page):
    page.m_ticker_input.setText("AMD")
    spy = QSignalSpy(page.research_requested)

    page.m_refresh_button.click()

    assert spy.count() == 1
    assert spy.at(0)[0].force_refresh is True


def test_daily_range_emitted_without_session(page):
    page.m_ticker_input.setText("MSFT")
    page.m_interval_combo.setCurrentIndex(6)
    page.m_start_date.setDate(QDate(2026, 10, 1))
    page.m_end_date.setDate(QDate(2026, 10, 30))
    spy = QSignalSpy(page.research_requested)

    page.m_analyze_button.click()

    assert spy.count() == 1
    request = spy.at(0)[0]
    assert request.start_date.isoformat() == "2026-10-01"
    assert request.end_date.isoformat() == "2026-10-30"
    assert request.session is None
    assert request.interval == ResearchInterval.DAILY


def test_blank_ticker_rejected_without_signal(page):
    spy = QSignalSpy(page.research_requested)
    page.m_analyze_button.click()
    assert spy.count() == 0
    assert "cannot be empty" in page.m_status_label.text()


def test_reversed_date_range_rejected_without_signal(page):
    page.m_ticker_input.setText("AMD")
    page.m_interval_combo.setCurrentIndex(6)
    page.m_start_date.setDate(QDate(2026, 10, 30))
    page.m_end_date.setDate(QDate(2026, 10, 1))
    spy = QSignalSpy(page.research_requested)

    page.m_analyze_button.click()

    assert spy.count() == 0
    assert "Start date" in page.m_status_label.text()


def test_running_blocks_requests_and_restores_controls(page):
    page.m_ticker_input.setText("AMD")
    spy = QSignalSpy(page.research_requested)
    page.set_running(True)
    assert not page.m_analyze_button.isEnabled()
    assert not page.m_refresh_button.isEnabled()
    page._request_research(force_refresh=False)
    assert spy.count() == 0

    page.set_running(False)
    assert page.m_analyze_button.isEnabled()
    assert page.m_refresh_button.isEnabled()
    assert not page.m_end_date.isEnabled()
    page.m_analyze_button.click()
    assert spy.count() == 1


def test_initial_presentation_is_ready(page):
    assert page.m_presentation_state == "ready"
    assert page.m_status_label.text() == "SYSTEM READY"
    assert page.m_analyze_button.isEnabled()


def test_loading_disables_actions_and_updates_regions(page):
    page.show_loading()
    assert page.m_presentation_state == "loading"
    assert page.m_running
    assert not page.m_analyze_button.isEnabled()
    assert not page.m_refresh_button.isEnabled()
    assert "Preparing" in page.m_chart_message.text()


def test_valid_request_enters_pending_state(page):
    page.m_ticker_input.setText("AMD")
    spy = QSignalSpy(page.research_requested)
    page.m_analyze_button.click()
    assert spy.count() == 1
    assert page.m_presentation_state == "loading"
    assert not page.m_analyze_button.isEnabled()


def test_empty_and_error_states_restore_controls(page):
    page.show_loading()
    page.show_empty("No candles in selected range.")
    assert page.m_presentation_state == "empty"
    assert "No candles" in page.m_chart_message.text()
    assert page.m_analyze_button.isEnabled()
    page.show_loading()
    page.show_error("Provider unavailable.")
    assert page.m_presentation_state == "error"
    assert "Provider unavailable" in page.m_chart_message.text()
    assert page.m_refresh_button.isEnabled()


def test_ready_clears_previous_error(page):
    page.show_error("Temporary failure")
    page.show_ready()
    assert page.m_presentation_state == "ready"
    assert "Temporary failure" not in page.m_chart_message.text()


def _research_result(status, message=None):
    request = HistoricalResearchRequest(
        symbol="AMD",
        start_date=QDate(2026, 10, 30).toPython(),
        end_date=QDate(2026, 10, 30).toPython(),
        interval=ResearchInterval.ONE_MINUTE,
    )
    return HistoricalResearchResult(
        request=request,
        source_candles=[],
        display_candles=[],
        window_metrics=None,
        data_source=ResearchDataSource.CACHE,
        status=status,
        message=message,
    )


@pytest.mark.parametrize(
    ("status", "expected_state"),
    [
        (ResearchDataStatus.AVAILABLE, "available"),
        (ResearchDataStatus.PARTIAL, "partial"),
    ],
)
def test_result_presentation_states(page, status, expected_state):
    page.show_loading()
    page.show_result(_research_result(status))
    assert page.m_presentation_state == expected_state
    assert page.m_chart_message.text() == ("No display candles returned for this research window.")
    assert page.m_candlestick_chart.m_candles == []
    assert "Source: cache" in page.m_metrics_message.text()
    assert page.m_analyze_button.isEnabled()


@pytest.mark.parametrize(
    ("status", "expected_state"),
    [
        (ResearchDataStatus.UNAVAILABLE, "empty"),
        (ResearchDataStatus.ERROR, "error"),
    ],
)
def test_unavailable_and_error_results_route_to_correct_state(page, status, expected_state):
    page.show_loading()
    page.show_result(_research_result(status, "Backend message"))
    assert page.m_presentation_state == expected_state
    assert "Backend message" in page.m_chart_message.text()
    assert page.m_analyze_button.isEnabled()
