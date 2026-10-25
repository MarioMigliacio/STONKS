# =============================================================================
# File: test_scanner_cancellation.py
# Purpose: Tests cooperative cancellation in scanner coordination and filtering.
# =============================================================================

from threading import Event
from unittest.mock import patch

import pytest

from stonks.scanner import filters
from stonks.scanner.scanner_cancelled import ScannerCancelled
from stonks.scanner.scanner_coordinator import ScannerCoordinator
from stonks.scanner.scanner_strategy import ScannerStrategy


class FakeStrategy(ScannerStrategy):
    """
    Provide a predictable strategy for cancellation tests.

    Attributes:
        strategy_id: Unique fake strategy identifier.
        display_name: Display label for the fake strategy.
        call_count: Number of times scan has been invoked.
    """

    strategy_id = "fake"
    display_name = "Fake Scanner"

    def __init__(self) -> None:
        """Initialize the scan invocation counter."""
        self.call_count = 0

    def scan(self) -> list:
        """
        Count a scan invocation and return no matches.

        Returns:
            An empty candidate list.
        """
        self.call_count += 1
        return []


def test_coordinator_cancels_before_execution():
    """Verify pre-cancelled coordination never invokes a strategy."""
    event = Event()
    event.set()
    strategy = FakeStrategy()
    coordinator = ScannerCoordinator([strategy], cancel_event=event)

    with pytest.raises(ScannerCancelled):
        coordinator.scan()

    assert strategy.call_count == 0


def test_coordinator_runs_without_cancellation():
    """Verify an unset cancellation event permits normal execution."""
    strategy = FakeStrategy()
    coordinator = ScannerCoordinator([strategy], cancel_event=Event())

    assert coordinator.scan() == []
    assert strategy.call_count == 1


def test_scanner_cancels_before_first_api_call():
    """Verify a cancelled scan does not request any quote data."""
    event = Event()
    event.set()

    with patch("stonks.scanner.filters.get_quote") as get_quote:
        with pytest.raises(ScannerCancelled):
            filters.scan_stocks(cancel_event=event)

    get_quote.assert_not_called()
