# =============================================================================
# File: candlestick_chart.py
# Purpose: Provides a reusable PyQtGraph chart for normalized OHLC candles.
# =============================================================================

from typing import List, Optional

import pyqtgraph as pg
from PySide6.QtWidgets import QWidget

from stonks.gui.widgets.candlestick_item import CandlestickItem
from stonks.models.candle_data import CandleData


class CandlestickChart(pg.PlotWidget):
    """Provide a standalone plotting surface for OHLCV candle rendering.

    Attributes:
        m_plot_item:
            Plot area hosting candle graphics.

        m_candle_item:
            Current candle graphics item, or None when the chart is empty.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize an empty, themed chart surface without market data."""
        super().__init__(parent=parent)
        self.setObjectName("candlestickChart")
        self.setBackground("#192532")

        self.m_plot_item = self.getPlotItem()
        self.m_plot_item.setLabel("left", "Price")
        self.m_plot_item.setLabel("bottom", "Time")
        self.m_plot_item.showGrid(x=True, y=True, alpha=0.15)
        self.m_plot_item.setMouseEnabled(x=True, y=True)
        self.m_candle_item: Optional[CandlestickItem] = None

    def set_candles(self, candles: List[CandleData]) -> None:
        """Replace the rendered candles using already-prepared market data."""
        if self.m_candle_item is not None:
            self.m_plot_item.removeItem(self.m_candle_item)
            self.m_candle_item = None

        if not candles:
            return

        self.m_candle_item = CandlestickItem(candles)
        self.m_plot_item.addItem(self.m_candle_item)
        self.m_plot_item.autoRange()

    def clear_candles(self) -> None:
        """Remove existing candle graphics without changing chart styling."""
        self.set_candles([])
