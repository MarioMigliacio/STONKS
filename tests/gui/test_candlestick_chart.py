# =============================================================================
# File: test_candlestick_chart.py
# Purpose: Verifies standalone chart rendering and deterministic OHLC geometry.
# =============================================================================

from datetime import datetime, timedelta

import pyqtgraph as pg
import pytest
from PySide6.QtCore import QRectF

from stonks.gui.widgets.candlestick_chart import CandlestickChart
from stonks.gui.widgets.candlestick_item import CandlestickItem
from stonks.models.candle_data import CandleData


def _candle(index, opening, high, low, closing):
    return CandleData(
        timestamp=datetime(2026, 11, 2, 9, 30) + timedelta(minutes=index),
        open_price=opening,
        high_price=high,
        low_price=low,
        close_price=closing,
        volume=1000 + index,
    )


def test_chart_initializes_without_market_data(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    assert isinstance(chart, pg.PlotWidget)
    assert chart.objectName() == "candlestickChart"
    assert chart.m_plot_item is chart.getPlotItem()
    assert chart.m_plot_item.listDataItems() == []
    assert chart.m_candle_item is None


def test_chart_can_be_displayed_and_closed(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.show()
    assert chart.isVisible()
    chart.close()
    assert not chart.isVisible()


def test_candle_geometry_and_colors():
    bullish = _candle(0, 100, 104, 98, 103)
    bearish = _candle(1, 103, 105, 99, 101)
    doji = _candle(2, 101, 102, 100, 101)
    item = CandlestickItem([bullish, bearish, doji])

    assert item.candle_geometry(0) == (0.0, 98, 104, 100, 103)
    assert item.candle_geometry(1) == (1.0, 99, 105, 101, 103)
    assert item.candle_geometry(2) == (2.0, 100, 102, 101, 101)
    assert item.candle_color(bullish) == item.BULLISH_COLOR
    assert item.candle_color(bearish) == item.BEARISH_COLOR
    assert item.candle_color(doji) == item.NEUTRAL_COLOR
    assert item.boundingRect() == QRectF(-0.5, 98, 3, 7)


def test_chart_replaces_and_clears_candles(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles([_candle(0, 100, 102, 99, 101), _candle(1, 101, 103, 100, 102)])
    first = chart.m_candle_item
    assert first is not None
    assert len(first.m_candles) == 2
    assert first in chart.m_plot_item.items

    chart.set_candles([_candle(0, 102, 104, 101, 103)])
    assert chart.m_candle_item is not first
    assert first not in chart.m_plot_item.items
    assert len(chart.m_candle_item.m_candles) == 1

    chart.clear_candles()
    assert chart.m_candle_item is None
    assert first not in chart.m_plot_item.items


def test_empty_and_flat_datasets_are_safe(qtbot):
    chart = CandlestickChart()
    qtbot.addWidget(chart)
    chart.set_candles([])
    assert chart.m_candle_item is None
    chart.set_candles([_candle(0, 100, 100, 100, 100)])
    assert chart.m_candle_item.boundingRect().height() > 0


def test_body_width_validation():
    with pytest.raises(ValueError, match="body width"):
        CandlestickItem([], body_width=0)
