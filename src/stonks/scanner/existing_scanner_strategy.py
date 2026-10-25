# =============================================================================
# File: existing_scanner_strategy.py
# Purpose: Adapts the existing stock scanner to the strategy interface.
# =============================================================================

from threading import Event
from typing import Optional

from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner import filters
from stonks.scanner.scanner_strategy import ScannerStrategy


class ExistingScannerStrategy(ScannerStrategy):
    """
    Adapt the existing stock scanner to the common strategy contract.

    Preserves the current watchlist, market-data retrieval, filtering,
    and candidate enrichment behavior while supporting cooperative
    cancellation during background execution.

    Attributes:
        strategy_id:
            Unique identifier for the existing scanner.

        display_name:
            Human-readable name displayed in the Scanner Workspace.

        m_cancel_event:
            Optional event shared with the scanner execution controller.
    """

    strategy_id = "existing_scanner"
    display_name = "Standard Market Scanner"

    def __init__(self, cancel_event: Optional[Event] = None) -> None:
        """
        Initialize the existing scanner adapter.

        Args:
            cancel_event:
                Optional cooperative cancellation event. When omitted,
                the scanner retains its original CLI behavior.
        """
        self.m_cancel_event = cancel_event

    def scan(self) -> list[ScannerCandidate]:
        """
        Execute the existing stock scanner.

        Returns:
            list[ScannerCandidate]:
                Candidates matching the current scanner filters.

        Raises:
            ScannerCancelled:
                If cancellation is requested during scanning.
        """
        if self.m_cancel_event is None:
            return filters.scan_stocks()

        return filters.scan_stocks(cancel_event=self.m_cancel_event)
