# =============================================================================
# File: test_candle_time_axis.py
# Purpose: Verifies market-time labeling and native chart navigation settings.
# =============================================================================

from datetime import datetime
from zoneinfo import ZoneInfo

from stonks.gui.widgets.candle_time_axis import CandleTimeAxis
from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.models.candle_data import CandleData

MARKET_TZ = ZoneInfo("America/New_York")


def _candle(timestamp):
    return CandleData(
        timestamp=timestamp,
        open_price=100.0,
        high_price=102.0,
        low_price=99.0,
        close_price=101.0,
        volume=1000,
    )


def test_intraday_time_labels(qtbot):
    axis = CandleTimeAxis()
    axis.set_timestamps(
        [
            datetime(2026, 11, 2, 9, 30, tzinfo=MARKET_TZ),
            datetime(2026, 11, 2, 9, 35, tzinfo=MARKET_TZ),
        ]
    )
    assert axis.tickStrings([0.0, 1.0, 1.5, -1.0, 2.0], 1, 1) == ["09:30", "09:35", "", "", ""]


def test_multi_day_labels_preserve_trading_gaps(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles(
        [
            _candle(datetime(2026, 10, 30, 16, 0, tzinfo=MARKET_TZ)),
            _candle(datetime(2026, 11, 2, 9, 30, tzinfo=MARKET_TZ)),
        ]
    )
    assert chart.m_time_axis.tickStrings([0, 1], 1, 1) == [
        "Oct 30",
        "Nov 02",
    ]
    assert chart.m_candle_item.candle_geometry(1)[0] == 1.0


def test_replacing_and_clearing_candles_updates_axis(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)

    chart.set_candles([_candle(datetime(2026, 11, 2, 9, 30, tzinfo=MARKET_TZ))])
    assert chart.m_time_axis.tickStrings([0], 1, 1) == ["09:30"]

    chart.set_candles([_candle(datetime(2026, 11, 3, 10, 15, tzinfo=MARKET_TZ))])
    assert chart.m_time_axis.tickStrings([0], 1, 1) == ["10:15"]

    chart.clear_candles()
    assert chart.m_time_axis.tickStrings([0], 1, 1) == [""]
    assert chart.m_time_axis.m_timestamps == []


def test_native_navigation_enabled(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    assert chart.m_plot_item.getViewBox().state["mouseEnabled"] == [
        True,
        True,
    ]
