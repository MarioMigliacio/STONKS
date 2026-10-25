# =============================================================================
# File: test_existing_scanner_strategy.py
# Purpose: Tests the existing scanner strategy adapter.
# =============================================================================

from unittest.mock import patch

from stonks.scanner.existing_scanner_strategy import ExistingScannerStrategy
from stonks.scanner.scanner_coordinator import ScannerCoordinator
from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy


def test_existing_scanner_implements_strategy_contract():
    """Verify the adapter satisfies the scanner strategy interface."""
    strategy = ExistingScannerStrategy()

    assert isinstance(strategy, ScannerStrategy)
    assert strategy.strategy_id == "existing_scanner"
    assert strategy.display_name == "Standard Market Scanner"


def test_existing_scanner_delegates_to_pipeline():
    """Verify the adapter invokes the existing scanner function."""
    expected_candidates = []

    with patch(
        "stonks.scanner.existing_scanner_strategy.filters.scan_stocks",
        return_value=expected_candidates,
    ) as mock_scan:
        strategy = ExistingScannerStrategy()
        results = strategy.scan()

    mock_scan.assert_called_once_with()
    assert results is expected_candidates


def test_existing_scanner_runs_through_coordinator():
    """Verify the coordinator can execute the existing adapter."""
    with patch(
        "stonks.scanner.existing_scanner_strategy.filters.scan_stocks",
        return_value=[],
    ) as mock_scan:
        coordinator = ScannerCoordinator(
            strategies=[ExistingScannerStrategy()],
            match_mode=ScannerMatchMode.ANY,
        )

        results = coordinator.scan()

    mock_scan.assert_called_once_with()
    assert results == []
