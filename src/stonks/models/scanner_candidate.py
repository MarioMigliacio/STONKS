# =============================================================================
# File: scanner_candidate.py
# Purpose: Represents a stock candidate produced by the scanner.
# =============================================================================

from dataclasses import dataclass
from typing import Optional

from stonks.models.float_data import FloatData
from stonks.models.quote_data import QuoteData
from stonks.scanner.float_classification import FloatClassification


@dataclass
class ScannerCandidate:
    """
    Represents scanner market data assembled for a stock.

    Attributes:
        quote_data:
            Normalized market quote data retrieved from a provider API.

        float_data:
            Reported public-float data for a stock.

        float_turnover:
            Ratio of volume divided by Float to represent moving shares.

        float_classification:
            Human readable representation of Float data classified.
    """

    quote_data: QuoteData
    float_data: Optional[FloatData]
    float_turnover: Optional[float] = None
    float_classification: FloatClassification = FloatClassification.UNKNOWN

    def __str__(self) -> str:
        result = str(self.quote_data)

        if not self.float_data:
            return f"{result}\nFloat: Unavailable"

        result += f"\n{self.float_data}"

        if self.float_turnover is not None:
            result += f" | Float Turnover: {self.float_turnover:.2%}"

        result += f" | Float Class: {self.float_classification.value}"

        return result
