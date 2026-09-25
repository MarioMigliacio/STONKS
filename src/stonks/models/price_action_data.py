# =============================================================================
# File: price_action_data.py
# Purpose: Represents calculated price-action metrics for a market-data window.
# =============================================================================

from dataclasses import dataclass
from typing import Optional


@dataclass
class PriceActionData:
    """
    Represents calculated price action for a market-data window.

    Attributes:
        change_percent:
            Percentage price change across the analyzed candles.
        high_price:
            Highest price reached across the analyzed candles.
        low_price:
            Lowest price reached across the analyzed candles.
        range_percent:
            Percentage range between the period low and high.
    """

    change_percent: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    range_percent: Optional[float]
