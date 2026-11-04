# =============================================================================
# File: candlestick_theme.py
# Purpose: Centralizes PyQtGraph chart colors and candle inspection styling.
# =============================================================================

CHART_BACKGROUND = "#192532"
CHART_BULLISH = "#65d9b5"
CHART_BEARISH = "#f07178"
CHART_NEUTRAL = "#a9b8c8"
CHART_CROSSHAIR = "#a9b8c8"
CHART_GRID_ALPHA = 0.15

CANDLE_INSPECTION_THEME = """
QLabel#candleInspectionLabel {
    background-color: #101923;
    color: #e2ebf2;
    border: 1px solid #344658;
    border-radius: 4px;
    padding: 6px;
}
"""
