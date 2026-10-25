# =============================================================================
# File: scanner_strategy.py
# Purpose: Defines the common interface for stock scanner strategies.
# =============================================================================

from abc import ABC, abstractmethod

from stonks.models.scanner_candidate import ScannerCandidate


class ScannerStrategy(ABC):
    """
    Represent a stock scanner strategy.

    Each strategy identifies stocks matching its criteria and
    returns normalized ScannerCandidate objects.

    Attributes:
        strategy_id:
            Unique identifier used to distinguish scanner strategies.

        display_name:
            Human-readable strategy name for the desktop interface.
    """

    strategy_id: str
    display_name: str

    @abstractmethod
    def scan(self) -> list[ScannerCandidate]:
        """
        Execute the scanner strategy.

        Returns:
            list[ScannerCandidate]:
                Stocks matching the strategy's criteria.
        """
        raise NotImplementedError
