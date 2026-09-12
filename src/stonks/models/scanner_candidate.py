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
    float_turnover: Optional[float] = None

    def __str__(self) -> str:
        result = str(self.quote_data)

        if not self.float_data:
            return f"{result}\nFloat: Unavailable"

        result += f"\n{self.float_data}"

        if self.float_turnover is not None:
            result += f" | Float Turnover: {self.float_turnover:.2%}"

        return result
