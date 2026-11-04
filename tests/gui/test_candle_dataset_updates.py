# =============================================================================
# File: test_candle_dataset_updates.py
# Purpose: Verifies prepared timeframe replacement and chart edge-case handling.
# =============================================================================

from datetime import datetime, timedelta

import pytest

from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.models.candle_data import CandleData


def _candle(timestamp, price=100.0):
    return CandleData(
        timestamp=timestamp,
        open_price=price,
        high_price=price + 2.0,
        low_price=price - 1.0,
        close_price=price + 1.0,
        volume=1000,
    )


def _chart(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    return chart


def test_prepared_timeframe_replacement_resets_inspection_and_axis(qtbot):
    chart = _chart(qtbot)
    start = datetime(2026, 11, 2, 9, 30)
    minute_candles = [_candle(start + timedelta(minutes=i)) for i in range(30)]
    chart.set_candles(minute_candles)
    chart.inspect_position(29, 100)
    previous_item = chart.m_candle_item

    five_minute_candles = [_candle(start + timedelta(minutes=i * 5), 120) for i in range(6)]
    chart.set_candles(five_minute_candles)

    assert previous_item not in chart.m_plot_item.items
    assert len(chart.m_candles) == 6
    assert chart.m_candle_item is not previous_item
    assert chart.m_time_axis.m_timestamps == [c.timestamp for c in five_minute_candles]
    assert chart.m_inspection_label.text() == ""
    assert not chart.m_vertical_cursor.isVisible()
    assert chart.inspect_position(29, 120) is None
    assert chart.inspect_position(5, 120) is chart.m_candles[5]
    x_range, y_range = chart.m_plot_item.getViewBox().viewRange()
    assert x_range[0] <= 0 <= 5 <= x_range[1]
    assert y_range[0] <= 119 <= 122 <= y_range[1]


def test_empty_dataset_clears_viewport_and_stale_readout(qtbot):
    chart = _chart(qtbot)
    chart.set_candles([_candle(datetime(2026, 11, 2, 9, 30), 200)])
    chart.inspect_position(0, 200)
    chart.set_candles([])

    assert chart.m_candle_item is None
    assert chart.m_candles == []
    assert chart.m_time_axis.m_timestamps == []
    assert chart.m_inspection_label.text() == ""
    assert chart.inspect_position(0, 200) is None
    x_range, y_range = chart.m_plot_item.getViewBox().viewRange()
    assert x_range == pytest.approx([-0.5, 0.5])
    assert y_range == pytest.approx([0.0, 1.0])


def test_single_flat_candle_remains_renderable(qtbot):
    chart = _chart(qtbot)
    timestamp = datetime(2026, 11, 2, 9, 30)
    flat = CandleData(timestamp, 100.0, 100.0, 100.0, 100.0, 0)
    chart.set_candles([flat])

    assert chart.m_candle_item.boundingRect().height() > 0
    assert chart.inspect_position(0, 100) is flat
    assert "V: 0" in chart.m_inspection_label.text()


def test_irregular_trading_gaps_preserve_adjacent_positions(qtbot):
    chart = _chart(qtbot)
    friday = _candle(datetime(2026, 10, 30, 16, 0))
    monday = _candle(datetime(2026, 11, 2, 9, 30))
    chart.set_candles([friday, monday])

    assert chart.m_candle_item.candle_geometry(0)[0] == 0.0
    assert chart.m_candle_item.candle_geometry(1)[0] == 1.0
    assert chart.m_time_axis.tickStrings([0, 1], 1, 1) == ["Oct 30", "Nov 02"]
    assert chart.inspect_position(1, 100) is monday


def test_replacing_dataset_does_not_mutate_input(qtbot):
    chart = _chart(qtbot)
    candles = [_candle(datetime(2026, 11, 2, 9, 30))]
    original = [c.__dict__.copy() for c in candles]
    chart.set_candles(candles)
    chart.set_candles([_candle(datetime(2026, 11, 3, 9, 30))])
    assert [c.__dict__ for c in candles] == original
