# =============================================================================
# File: test_research_market_time_display.py
# Purpose: Verifies market timezone conversion and Refresh quota guidance.
# =============================================================================
from datetime import datetime, timezone

from stonks.gui.pages.research_page import ResearchPage
from stonks.gui.widgets.candle_time_axis import CandleTimeAxis
from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.models.candle_data import CandleData


def _candle(timestamp):
    return CandleData(timestamp, 100.0, 102.0, 99.0, 101.0, 1000)


def test_utc_regular_session_labels(qtbot):
    axis = CandleTimeAxis()
    axis.set_timestamps(
        [
            datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc),
            datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc),
        ]
    )
    assert axis.tickStrings([0, 1], 1, 1) == ["09:30", "16:00"]


def test_after_hours_crossing_utc_midnight(qtbot):
    axis = CandleTimeAxis()
    axis.set_timestamps(
        [
            datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc),
            datetime(2026, 11, 4, 0, 30, tzinfo=timezone.utc),
        ]
    )
    assert axis.tickStrings([0, 1], 1, 1) == ["16:00", "19:30"]


def test_inspection_market_time_preserves_source(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    timestamp = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)
    candle = _candle(timestamp)
    chart.set_candles([candle])
    chart.inspect_position(0, 101.0)
    assert "2026-11-03 09:30 EST" in chart.m_inspection_label.text()
    assert candle.timestamp == timestamp


def test_refresh_tooltip(qtbot):
    page = ResearchPage()
    qtbot.addWidget(page)
    tooltip = page.m_refresh_button.toolTip().lower()
    assert "cached" in tooltip
    assert "api request" in tooltip
