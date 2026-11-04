# =============================================================================
# File: test_candle_inspection.py
# Purpose: Verifies deterministic crosshair inspection and stale-state cleanup.
# =============================================================================

from datetime import datetime, timedelta, timezone

from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.models.candle_data import CandleData


def _candle(index):
    return CandleData(
        timestamp=datetime(2026, 11, 2, 9, 30, tzinfo=timezone.utc) + timedelta(minutes=index),
        open_price=100.0 + index,
        high_price=103.0 + index,
        low_price=99.0 + index,
        close_price=102.0 + index,
        volume=12345 + index,
    )


def test_inspection_shows_timestamp_ohlcv_and_guides(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles([_candle(0), _candle(1)])
    chart.show()

    assert chart.inspect_position(1.1, 102.5) is chart.m_candles[1]
    text = chart.m_inspection_label.text()
    assert "2026-11-02 09:31:00+00:00" in text
    assert "O: 101.00" in text
    assert "H: 104.00" in text
    assert "L: 100.00" in text
    assert "C: 103.00" in text
    assert "V: 12,346" in text
    assert chart.m_vertical_cursor.isVisible()
    assert chart.m_horizontal_cursor.isVisible()
    assert chart.m_vertical_cursor.value() == 1.0
    assert chart.m_horizontal_cursor.value() == 102.5


def test_outside_dataset_hides_inspection(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles([_candle(0)])
    chart.inspect_position(0, 100)
    assert chart.inspect_position(1, 100) is None
    assert not chart.m_inspection_label.isVisible()
    assert not chart.m_vertical_cursor.isVisible()
    assert not chart.m_horizontal_cursor.isVisible()
    assert chart.m_inspection_label.text() == ""


def test_replacement_and_clear_discard_stale_inspection(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles([_candle(0), _candle(1)])
    chart.inspect_position(1, 101)
    chart.set_candles([_candle(0)])
    assert chart.m_inspection_label.text() == ""
    assert chart.inspect_position(1, 101) is None
    chart.inspect_position(0, 101)
    chart.clear_candles()
    assert chart.inspect_position(0, 101) is None
    assert chart.m_candles == []


def test_inspection_does_not_mutate_source_candles(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    candle = _candle(0)
    original = candle.__dict__.copy()
    chart.set_candles([candle])
    chart.inspect_position(0, 101)
    assert candle.__dict__ == original


def test_resize_during_initialization_is_safe(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)

    chart.resize(800, 500)
    chart.show()

    assert chart.m_inspection_label is not None
