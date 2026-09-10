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
    """Represents scanner market data assembled for a stock."""

    quote_data: QuoteData
    float_data: Optional[FloatData]
