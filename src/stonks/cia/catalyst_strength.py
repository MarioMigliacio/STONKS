# =============================================================================
# File: catalyst_strength.py
# Purpose: Defines catalyst strength levels used by the STONKS C.I.A.
# =============================================================================

from enum import Enum


class CatalystStrength(Enum):
    """Represents the assessed strength of a catalyst."""

    UNKNOWN = "Unknown"
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"