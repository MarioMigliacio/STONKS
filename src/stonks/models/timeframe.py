# =============================================================================
# File: timeframe.py
# Purpose: Defines the candle intervals used throughout STONKS
# =============================================================================

from enum import Enum


class Timeframe(Enum):
    """Represents a supported market-data candle interval."""

    ONE_MINUTE = "1min"
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    THIRTY_MINUTES = "30min"
    SIXTY_MINUTES = "60min"
    DAILY = "daily"
