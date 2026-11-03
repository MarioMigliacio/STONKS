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
