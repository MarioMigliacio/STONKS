# =============================================================================
# File: scanner_candidate.py
# Purpose: Represents a stock candidate produced by the scanner.
# =============================================================================

from dataclasses import dataclass
from typing import Optional

from stonks.models.float_data import FloatData
from stonks.models.quote_data import QuoteData


@dataclass
class ScannerCandidate:
    """
    Represents scanner market data assembled for a stock.

    Attributes:
        quote_data:
            Normalized market quote data retrieved from a provider API.

        float_data:
            Reported public-float data for a stock.
    """

    quote_data: QuoteData
    float_data: Optional[FloatData]

    def __str__(self) -> str:
        if self.float_data:
            return f"{self.quote_data}\n{self.float_data}"

        return f"{self.quote_data}\nFloat: Unavailable"
