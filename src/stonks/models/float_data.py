# =============================================================================
# File: float_data.py
# Purpose: Represents public-float data for a stock.
# =============================================================================

from dataclasses import dataclass
from datetime import date


@dataclass
class FloatData:
    """
    Represents reported public-float data for a stock.

    Attributes:
        symbol:
            Stock ticker symbol.

        float_shares:
            Physical count of shares as reported by API.

        float_percent:
            Percentage of the company's total shares outstanding, considered freely tradable by the public as
            reported by API.

        effective_date:
            From the date of which the Float data was reported at.

        source:
            Originating source of data, string format.
    """

    symbol: str
    float_shares: int
    float_percent: float
    effective_date: date
    source: str

    def __str__(self) -> str:
        return (
            f"Float: {self.float_shares:,} | "
            f"Float %: {self.float_percent:.2f}% | "
            f"Effective: {self.effective_date} | "
            f"Source: {self.source}"
        )
