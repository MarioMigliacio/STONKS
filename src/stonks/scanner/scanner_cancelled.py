# =============================================================================
# File: scanner_cancelled.py
# Purpose: Defines the exception raised when scanner execution is cancelled.
# =============================================================================


class ScannerCancelled(Exception):
    """Represent a scanner run stopped through cooperative cancellation."""
