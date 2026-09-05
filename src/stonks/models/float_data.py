# =============================================================================
# File: float_data.py
# Purpose: Represents public-float data for a stock.
# =============================================================================

from dataclasses import dataclass
from datetime import date


@dataclass
class FloatData:
    """Represents reported public-float data for a stock."""

    symbol: str
    float_shares: int
    float_percent: float
    effective_date: date
    source: str
