# =============================================================================
# File: test_research_chart_integration.py
# Purpose: Verifies ResearchPage chart lifecycle and prepared-data rendering.
# =============================================================================

from datetime import datetime, timedelta

import pytest
from PySide6.QtCore import QDate

from stonks.gui.pages.research_page import ResearchPage
from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.models.candle_data import CandleData
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.research_interval import ResearchInterval


@pytest.fixture
def page(qtbot):
    widget = ResearchPage()
    qtbot.addWidget(widget)
    return widget


def _candles(count):
    start = datetime(2026, 10, 30, 9, 30)
    return [
        CandleData(
            timestamp=start + timedelta(minutes=index),
            open_price=100.0 + index,
            high_price=102.0 + index,
            low_price=99.0 + index,
            close_price=101.0 + index,
            volume=1000 + index,
        )
        for index in range(count)
    ]


def _result(candles, status=ResearchDataStatus.AVAILABLE):
    request = HistoricalResearchRequest(
        symbol="AMD",
        start_date=QDate(2026, 10, 30).toPython(),
        end_date=QDate(2026, 10, 30).toPython(),
        interval=ResearchInterval.ONE_MINUTE,
    )
    return HistoricalResearchResult(
        request=request,
        source_candles=list(candles),
        display_candles=list(candles),
        window_metrics=None,
        data_source=ResearchDataSource.CACHE,
        status=status,
    )


def test_chart_is_embedded_but_initially_empty(page):
    assert isinstance(page.m_candlestick_chart, CandlestickChart)
    assert page.m_candlestick_chart.m_candles == []
    assert page.m_chart_message.text()


@pytest.mark.parametrize("status", [ResearchDataStatus.AVAILABLE, ResearchDataStatus.PARTIAL])
def test_available_results_render_prepared_candles(page, status):
    candles = _candles(3)
    page.show_result(_result(candles, status))
    assert page.m_candlestick_chart.m_candles == candles
    assert page.m_candlestick_chart.m_candle_item is not None
    assert not page.m_candlestick_chart.isHidden()
    assert page.m_chart_message.isHidden()
    assert "Source: cache" in page.m_metrics_message.text()


def test_replacement_and_empty_available_result(page):
    page.show_result(_result(_candles(4)))
    page.show_result(_result(_candles(1)))
    assert len(page.m_candlestick_chart.m_candles) == 1
    page.show_result(_result([]))
    assert page.m_candlestick_chart.m_candles == []
    assert page.m_candlestick_chart.isHidden()
    assert "No display candles" in page.m_chart_message.text()


@pytest.mark.parametrize("transition", ["show_ready", "show_loading", "show_empty", "show_error"])
def test_transitions_clear_stale_chart(page, transition):
    page.show_result(_result(_candles(2)))
    if transition == "show_error":
        page.show_error("Simulated research failure.")
    else:
        getattr(page, transition)()
    assert page.m_candlestick_chart.m_candles == []
    assert page.m_candlestick_chart.isHidden()
