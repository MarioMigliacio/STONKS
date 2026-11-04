# =============================================================================
# File: candlestick_item.py
# Purpose: Renders normalized OHLC candles as a reusable Qt graphics item.
# =============================================================================

from typing import List, Tuple

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsObject, QWidget

from stonks.models.candle_data import CandleData


class CandlestickItem(QGraphicsObject):
    """Render candle bodies and wicks at consecutive integer x positions.

    Attributes:
        m_candles:
            Snapshot of the candles rendered by this item.

        m_body_width:
            Horizontal width of each candle body in index units.
    """

    BULLISH_COLOR = QColor("#65d9b5")
    BEARISH_COLOR = QColor("#f07178")
    NEUTRAL_COLOR = QColor("#a9b8c8")

    def __init__(self, candles: List[CandleData], body_width: float = 0.7) -> None:
        """Create a candle graphics item without accessing external data."""
        super().__init__()
        if not 0.0 < body_width <= 1.0:
            raise ValueError("Candle body width must be greater than zero and at most one.")

        self.m_candles = list(candles)
        self.m_body_width = body_width

    def boundingRect(self) -> QRectF:
        """Return the full price/index extent, including wick endpoints."""
        if not self.m_candles:
            return QRectF()

        minimum = min(candle.low_price for candle in self.m_candles)
        maximum = max(candle.high_price for candle in self.m_candles)

        # A flat dataset must still have a nonzero bounding rectangle.
        if minimum == maximum:
            padding = max(abs(minimum) * 0.001, 0.01)
            minimum -= padding
            maximum += padding
        return QRectF(-0.5, minimum, float(len(self.m_candles)), maximum - minimum)

    def candle_geometry(self, index: int) -> Tuple[float, float, float, float, float]:
        """Return (x, low, high, body_bottom, body_top) for one candle."""
        candle = self.m_candles[index]

        return (
            float(index),
            candle.low_price,
            candle.high_price,
            min(candle.open_price, candle.close_price),
            max(candle.open_price, candle.close_price),
        )

    @classmethod
    def candle_color(cls, candle: CandleData) -> QColor:
        """Choose the color from the candle's opening and closing prices."""
        if candle.close_price > candle.open_price:
            return cls.BULLISH_COLOR
        if candle.close_price < candle.open_price:
            return cls.BEARISH_COLOR
        return cls.NEUTRAL_COLOR

    def paint(self, painter: QPainter, option, widget: QWidget = None) -> None:
        """Draw a wick and filled body for every candle; dojis use a line."""
        del option, widget
        painter.save()
        for index, candle in enumerate(self.m_candles):
            x, low, high, body_bottom, body_top = self.candle_geometry(index)
            color = self.candle_color(candle)
            painter.setPen(QPen(color, 0))
            painter.drawLine(x, low, x, high)

            if body_bottom == body_top:
                painter.drawLine(
                    x - self.m_body_width / 2.0,
                    body_bottom,
                    x + self.m_body_width / 2.0,
                    body_top,
                )
            else:
                painter.setBrush(color)
                painter.drawRect(
                    QRectF(
                        x - self.m_body_width / 2.0,
                        body_bottom,
                        self.m_body_width,
                        body_top - body_bottom,
                    )
                )
        painter.restore()
