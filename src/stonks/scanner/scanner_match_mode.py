# =============================================================================
# File: scanner_match_mode.py
# Purpose: Defines how results from multiple scanners are combined.
# =============================================================================

from enum import Enum


class ScannerMatchMode(Enum):
    """
    Define how multiple scanner strategy results are combined.

    Attributes:
        ANY:
            Include stocks matching at least one selected strategy.

        ALL:
            Include only stocks matching every selected strategy.
    """

    ANY = "ANY"
    ALL = "ALL"
