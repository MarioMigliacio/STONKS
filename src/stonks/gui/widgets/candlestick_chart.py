# =============================================================================
# File: candlestick_chart.py
# Purpose: Provides a reusable PyQtGraph chart for normalized OHLC candles.
# =============================================================================

from typing import List, Optional

import pyqtgraph as pg
from PySide6.QtWidgets import QWidget

from stonks.gui.widgets.candle_time_axis import CandleTimeAxis
from stonks.gui.widgets.candlestick_item import CandlestickItem
from stonks.models.candle_data import CandleData


class CandlestickChart(pg.PlotWidget):
    """Provide a standalone plotting surface for OHLCV candle rendering.

    Attributes:
        m_plot_item:
            Plot area hosting candle graphics.

        m_candle_item:
            Current candle graphics item, or None when the chart is empty.

        m_time_axis:
            Bottom axis translating candle indices into market timestamps.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize an empty, themed chart surface without market data."""
        self.m_time_axis = CandleTimeAxis()
        super().__init__(parent=parent, axisItems={"bottom": self.m_time_axis})
        self.setObjectName("candlestickChart")
        self.setBackground("#192532")

        self.m_plot_item = self.getPlotItem()
        self.m_plot_item.setLabel("left", "Price")
        self.m_plot_item.setLabel("bottom", "Time")
        self.m_plot_item.showGrid(x=True, y=True, alpha=0.15)
        self.m_plot_item.setMouseEnabled(x=True, y=True)
        self.m_candle_item: Optional[CandlestickItem] = None

    def set_candles(self, candles: List[CandleData]) -> None:
        """Replace rendered candles and update timestamp labels atomically."""
        if self.m_candle_item is not None:
            self.m_plot_item.removeItem(self.m_candle_item)
            self.m_candle_item = None

        self.m_time_axis.set_timestamps([candle.timestamp for candle in candles])
        if not candles:
            return

        self.m_candle_item = CandlestickItem(candles)
        self.m_plot_item.addItem(self.m_candle_item)
        self.m_plot_item.autoRange()

    def clear_candles(self) -> None:
        """Remove existing candle graphics and stale time labels."""
        self.set_candles([])
