# =============================================================================
# File: candlestick_chart.py
# Purpose: Provides a reusable PyQtGraph chart with OHLCV cursor inspection.
# =============================================================================

from typing import List, Optional

import pyqtgraph as pg
from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QLabel, QWidget

from stonks.gui.widgets.candle_time_axis import CandleTimeAxis
from stonks.gui.widgets.candlestick_item import CandlestickItem
from stonks.models.candle_data import CandleData


class CandlestickChart(pg.PlotWidget):
    """Render prepared candles and inspect OHLCV values without changing data.

    Attributes:
        m_plot_item:
            Plot area hosting candle graphics.

        m_candle_item:
            Current candle graphics item, or None when empty.

        m_time_axis:
            Bottom axis mapping indices to market timestamps.

        m_candles:
            Snapshot of the currently displayed candle sequence.

        m_vertical_cursor:
            Vertical inspection guide.

        m_horizontal_cursor:
            Horizontal inspection guide.

        m_inspection_label:
            Read-only OHLCV inspection overlay.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize a themed chart with hidden inspection guides."""
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
        self.m_candles: List[CandleData] = []

        guide_pen = pg.mkPen("#a9b8c8", width=1, style=Qt.DashLine)
        self.m_vertical_cursor = pg.InfiniteLine(angle=90, movable=False, pen=guide_pen)
        self.m_horizontal_cursor = pg.InfiniteLine(angle=0, movable=False, pen=guide_pen)
        self.m_plot_item.addItem(self.m_vertical_cursor, ignoreBounds=True)
        self.m_plot_item.addItem(self.m_horizontal_cursor, ignoreBounds=True)
        self.m_vertical_cursor.hide()
        self.m_horizontal_cursor.hide()

        self.m_inspection_label = QLabel(self)
        self.m_inspection_label.setObjectName("candleInspectionLabel")
        self.m_inspection_label.setStyleSheet(
            "QLabel { background: #101923; color: #e2ebf2; "
            "border: 1px solid #344658; border-radius: 4px; padding: 6px; }"
        )
        self.m_inspection_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.m_inspection_label.hide()
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def set_candles(self, candles: List[CandleData]) -> None:
        """Replace candle data, time labels, and stale inspection state."""
        self.clear_inspection()
        if self.m_candle_item is not None:
            self.m_plot_item.removeItem(self.m_candle_item)
            self.m_candle_item = None

        self.m_candles = list(candles)
        self.m_time_axis.set_timestamps([candle.timestamp for candle in self.m_candles])
        if not self.m_candles:
            return

        self.m_candle_item = CandlestickItem(self.m_candles)
        self.m_plot_item.addItem(self.m_candle_item)
        self.m_plot_item.autoRange()

    def clear_candles(self) -> None:
        """Remove existing graphics, timestamps, and inspection state."""
        self.set_candles([])

    def inspect_position(self, x: float, price: float) -> Optional[CandleData]:
        """Inspect the nearest candle only within its half-index footprint."""
        index = round(x)
        if abs(x - index) > 0.5 or not 0 <= index < len(self.m_candles):
            self.clear_inspection()
            return None

        candle = self.m_candles[index]
        self.m_vertical_cursor.setPos(float(index))
        self.m_horizontal_cursor.setPos(price)
        self.m_vertical_cursor.show()
        self.m_horizontal_cursor.show()
        self.m_inspection_label.setText(
            f"{candle.timestamp.isoformat(sep=' ')}  |  "
            f"O: {candle.open_price:.2f}  H: {candle.high_price:.2f}  "
            f"L: {candle.low_price:.2f}  C: {candle.close_price:.2f}  "
            f"V: {candle.volume:,}"
        )
        self.m_inspection_label.adjustSize()
        self._position_inspection_label()
        self.m_inspection_label.show()
        return candle

    def clear_inspection(self) -> None:
        """Hide the crosshair and readout when no candle is selected."""
        self.m_vertical_cursor.hide()
        self.m_horizontal_cursor.hide()
        self.m_inspection_label.hide()
        self.m_inspection_label.clear()

    def _on_mouse_moved(self, scene_position: QPointF) -> None:
        """Translate scene coordinates to the chart's index/price space."""
        view_box = self.m_plot_item.getViewBox()
        if not view_box.sceneBoundingRect().contains(scene_position):
            self.clear_inspection()
            return
        position = view_box.mapSceneToView(scene_position)
        self.inspect_position(position.x(), position.y())

    def _position_inspection_label(self) -> None:
        """Keep the readout inside the widget's top edge."""
        self.m_inspection_label.move(max(4, self.width() - self.m_inspection_label.width() - 8), 8)

    def resizeEvent(self, event) -> None:
        """Reposition the inspection overlay after initialization."""
        super().resizeEvent(event)

        if hasattr(self, "m_inspection_label"):
            self._position_inspection_label()
