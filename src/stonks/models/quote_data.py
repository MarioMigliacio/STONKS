# =============================================================================
# File: quote_data.py
# Purpose: Normalized market quote data model.
#
# Notes:
# - This model acts as the abstraction layer between external API payloads
#   and internal scanner logic.
# - Scanner systems should consume QuoteData objects rather than raw JSON.
# =============================================================================

from dataclasses import dataclass

@dataclass
class QuoteData:
    """
    Represents normalized market quote data retrieved from a provider API.

    Attributes:
        symbol:
            Stock ticker symbol.

        price:
            Current market price.

        volume:
            Current daily trading volume.

        change_percent:
            Percentage change from previous close.

        gap_percent:
            Percentage difference between today's open and previous close.
    """

    symbol: str
    price: float
    volume: int
    change_percent: float
    gap_percent: float

    def __repr__(self):
        return (
            f"{self.symbol} | "
            f"Price: ${self.price:.2f} | "
            f"Volume: {self.volume:,} | "
            f"Change: {self.change_percent:+.2f}% | "
            f"Gap: {self.gap_percent:+.2f}%"
        )