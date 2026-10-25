# =============================================================================
# File: scanner_coordinator.py
# Purpose: Combines scanner strategy matches using ANY or ALL matching.
# =============================================================================

from collections import Counter
from threading import Event
from typing import Optional

from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_cancelled import ScannerCancelled
from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy


class ScannerCoordinator:
    """
    Coordinate selected scanner strategies and combine their candidates.

    Attributes:
        m_strategies:
            Selected scanner strategies.

        m_match_mode:
            Rule for combining strategy matches.

        m_cancel_event:
            Optional event shared with the worker and strategies.
    """

    def __init__(
        self,
        strategies: list[ScannerStrategy],
        match_mode: ScannerMatchMode = ScannerMatchMode.ANY,
        cancel_event: Optional[Event] = None,
    ) -> None:
        """
        Initialize scanner execution settings.

        Args:
            strategies:
                Strategies to execute in sequence.

            match_mode:
                ANY union or ALL intersection.

            cancel_event:
                Optional cooperative cancellation event.

        Raises:
            ValueError: If no strategies or duplicate strategy IDs are supplied.
        """
        if not strategies:
            raise ValueError("At least one scanner strategy is required.")

        strategy_ids = [strategy.strategy_id for strategy in strategies]
        if len(strategy_ids) != len(set(strategy_ids)):
            raise ValueError("Scanner strategy IDs must be unique.")

        self.m_strategies = strategies
        self.m_match_mode = match_mode
        self.m_cancel_event = cancel_event

    def _check_cancelled(self) -> None:
        """
        Reject further work when cancellation is requested.

        Raises:
            ScannerCancelled: If the shared event has been set.
        """
        if self.m_cancel_event is not None and self.m_cancel_event.is_set():
            raise ScannerCancelled("Scanner execution cancelled.")

    def scan(self) -> list[ScannerCandidate]:
        """
        Execute strategies and combine their results by normalized ticker.

        Returns:
            Unique candidates matching the selected ANY or ALL rule.

        Raises:
            ScannerCancelled: If cancellation is requested between operations.
        """
        candidates = {}
        match_counts = Counter()

        self._check_cancelled()

        for strategy in self.m_strategies:
            self._check_cancelled()
            strategy_matches = set()

            for candidate in strategy.scan():
                self._check_cancelled()
                symbol = candidate.quote_data.symbol.strip().upper()

                if not symbol or symbol in strategy_matches:
                    continue

                strategy_matches.add(symbol)
                match_counts[symbol] += 1
                candidates.setdefault(symbol, candidate)

        self._check_cancelled()

        required_matches = 1 if self.m_match_mode == ScannerMatchMode.ANY else len(self.m_strategies)
        return [candidate for symbol, candidate in candidates.items() if match_counts[symbol] >= required_matches]
