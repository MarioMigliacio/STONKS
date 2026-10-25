# =============================================================================
# File: existing_scanner_strategy.py
# Purpose: Adapts the existing stock scanner to the strategy interface.
# =============================================================================

from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner import filters
from stonks.scanner.scanner_strategy import ScannerStrategy


class ExistingScannerStrategy(ScannerStrategy):
    """
    Adapt the existing stock scanner to the common strategy contract.

    Preserves the current watchlist, market-data retrieval, filtering,
    and candidate enrichment behavior.

    Attributes:
        strategy_id:
            Unique identifier for the existing scanner.

        display_name:
            Human-readable name displayed in the Scanner Workspace.
    """

    strategy_id = "existing_scanner"
    display_name = "Standard Market Scanner"

    def scan(self) -> list[ScannerCandidate]:
        """
        Execute the existing stock scanner.

        Returns:
            list[ScannerCandidate]:
                Candidates matching the current scanner filters.
        """
        return filters.scan_stocks()
