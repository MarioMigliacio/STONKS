# =============================================================================
# File: candle_data.py
# Purpose: Defines the representation of OHLCV market data.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CandleData:
    """
    Represents OHLCV market data for a single trading period.

    Attributes:
        timestamp:
            Date and time associated with the candle.

        open_price:
            Price at the beginning of the trading period.

        high_price:
            Highest price reached during the trading period.

        low_price:
            Lowest price reached during the trading period.

        close_price:
            Price at the end of the trading period.

        volume:
            Total trading volume during the trading period.
    """

    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
