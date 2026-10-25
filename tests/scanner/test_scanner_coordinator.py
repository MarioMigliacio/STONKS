# =============================================================================
# File: test_scanner_coordinator.py
# Purpose: Tests scanner coordination and ANY/ALL result matching.
# =============================================================================

import pytest

from stonks.models.quote_data import QuoteData
from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_coordinator import ScannerCoordinator
from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy


class FakeScannerStrategy(ScannerStrategy):
    """Provide predetermined scanner candidates for unit testing."""

    def __init__(self, strategy_id: str, symbols: list[str]) -> None:
        self.strategy_id = strategy_id
        self.display_name = strategy_id
        self.symbols = symbols

    def scan(self) -> list[ScannerCandidate]:
        """Return synthetic candidates without making API calls."""
        return [make_candidate(symbol) for symbol in self.symbols]


def make_candidate(symbol: str) -> ScannerCandidate:
    """Create a minimal normalized scanner candidate."""
    return ScannerCandidate(
        quote_data=QuoteData(
            symbol=symbol,
            price=100.0,
            volume=1_000_000,
            change_percent=5.0,
            gap_percent=2.0,
            latest_trading_day="2026-10-23",
        ),
        float_data=None,
    )


def symbols_of(candidates: list[ScannerCandidate]) -> list[str]:
    """Extract candidate symbols for readable assertions."""
    return [candidate.quote_data.symbol for candidate in candidates]


def test_any_mode_combines_unique_candidates():
    """ANY should return the union of selected scanner results."""
    strategies = [
        FakeScannerStrategy("momentum", ["AAPL", "NVDA"]),
        FakeScannerStrategy("volume", ["NVDA", "TSLA"]),
    ]

    coordinator = ScannerCoordinator(strategies, ScannerMatchMode.ANY)

    assert symbols_of(coordinator.scan()) == ["AAPL", "NVDA", "TSLA"]


def test_all_mode_returns_shared_candidates():
    """ALL should return only stocks matched by every scanner."""
    strategies = [
        FakeScannerStrategy("momentum", ["AAPL", "NVDA", "AMD"]),
        FakeScannerStrategy("volume", ["NVDA", "AMD", "TSLA"]),
        FakeScannerStrategy("breakout", ["NVDA", "AMD", "META"]),
    ]

    coordinator = ScannerCoordinator(strategies, ScannerMatchMode.ALL)

    assert symbols_of(coordinator.scan()) == ["NVDA", "AMD"]


def test_all_mode_with_no_common_candidates():
    """ALL should return an empty list when nothing matches."""
    strategies = [
        FakeScannerStrategy("momentum", ["AAPL"]),
        FakeScannerStrategy("volume", ["TSLA"]),
    ]

    coordinator = ScannerCoordinator(strategies, ScannerMatchMode.ALL)

    assert coordinator.scan() == []


def test_duplicate_tickers_count_once_per_strategy():
    """Repeated symbols must not inflate strategy match counts."""
    strategies = [
        FakeScannerStrategy("momentum", ["NVDA", "NVDA"]),
        FakeScannerStrategy("volume", ["TSLA"]),
    ]

    coordinator = ScannerCoordinator(strategies, ScannerMatchMode.ALL)

    assert coordinator.scan() == []


def test_empty_strategy_list_rejected():
    """A coordinator must have at least one selected strategy."""
    with pytest.raises(ValueError, match="At least one"):
        ScannerCoordinator([])


def test_duplicate_strategy_ids_rejected():
    """Two strategies cannot share the same identifier."""
    strategies = [
        FakeScannerStrategy("momentum", ["AAPL"]),
        FakeScannerStrategy("momentum", ["NVDA"]),
    ]

    with pytest.raises(ValueError, match="unique"):
        ScannerCoordinator(strategies)


def test_single_strategy_works_with_all_mode():
    """A single strategy should work in either matching mode."""
    strategies = [FakeScannerStrategy("momentum", ["AAPL", "NVDA"])]

    coordinator = ScannerCoordinator(strategies, ScannerMatchMode.ALL)

    assert symbols_of(coordinator.scan()) == ["AAPL", "NVDA"]
