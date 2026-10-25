# =============================================================================
# File: test_scanner_contracts.py
# Purpose: Validates scanner strategy contracts and matching modes.
# =============================================================================

import pytest

from stonks.scanner.scanner_match_mode import ScannerMatchMode
from stonks.scanner.scanner_strategy import ScannerStrategy


def test_scanner_match_modes():
    """Verify the supported scanner combination modes."""
    assert ScannerMatchMode.ANY.value == "ANY"
    assert ScannerMatchMode.ALL.value == "ALL"


def test_scanner_strategy_cannot_be_instantiated():
    """Verify abstract scanner strategies cannot be instantiated."""
    with pytest.raises(TypeError):
        ScannerStrategy()


def test_scanner_strategy_requires_scan_implementation():
    """Verify concrete strategies must implement scan()."""

    class IncompleteStrategy(ScannerStrategy):
        strategy_id = "incomplete"
        display_name = "Incomplete Scanner"

    with pytest.raises(TypeError):
        IncompleteStrategy()
