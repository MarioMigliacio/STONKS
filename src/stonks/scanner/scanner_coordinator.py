# =============================================================================
# File: scanner_coordinator.py
# Purpose: Coordinates scanner strategies and combines their results.
# =============================================================================

from collections import Counter

from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy


class ScannerCoordinator:
    """
    Coordinate execution and result matching across scanner strategies.

    Attributes:
        m_strategies:
            Selected scanner strategies to execute.

        m_match_mode:
            Determines whether ANY or ALL strategies must match.
    """

    def __init__(
        self,
        strategies: list[ScannerStrategy],
        match_mode: ScannerMatchMode = ScannerMatchMode.ANY,
    ) -> None:
        """
        Initialize the scanner coordinator.

        Args:
            strategies:
                Scanner strategies selected for execution.

            match_mode:
                Rule used to combine scanner results.

        Raises:
            ValueError:
                If no strategies are provided or strategy IDs are duplicated.
        """
        if not strategies:
            raise ValueError("At least one scanner strategy is required.")

        strategy_ids = [strategy.strategy_id for strategy in strategies]

        if len(strategy_ids) != len(set(strategy_ids)):
            raise ValueError("Scanner strategy IDs must be unique.")

        self.m_strategies = strategies
        self.m_match_mode = match_mode

    def scan(self) -> list[ScannerCandidate]:
        """
        Execute selected scanners and combine their candidates.

        Each strategy contributes at most one match per ticker.
        Candidates are deduplicated using their normalized symbol.

        Returns:
            list[ScannerCandidate]:
                Unique candidates matching the selected combination mode.
        """
        candidates = {}
        match_counts = Counter()

        for strategy in self.m_strategies:
            strategy_matches = set()

            for candidate in strategy.scan():
                symbol = candidate.quote_data.symbol.strip().upper()

                if not symbol:
                    continue

                if symbol in strategy_matches:
                    continue

                strategy_matches.add(symbol)
                match_counts[symbol] += 1

                # Preserve the first candidate returned for each symbol.
                candidates.setdefault(symbol, candidate)

        required_matches = 1 if self.m_match_mode == ScannerMatchMode.ANY else len(self.m_strategies)

        return [candidate for symbol, candidate in candidates.items() if match_counts[symbol] >= required_matches]
