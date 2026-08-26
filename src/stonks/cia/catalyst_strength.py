# =============================================================================
# File: catalyst_strength.py
# Purpose: Defines catalyst strength levels used by the STONKS C.I.A.
# =============================================================================

from enum import Enum

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_freshness import CatalystFreshness


class CatalystStrength(Enum):
    """Represents the assessed strength of a catalyst."""

    UNKNOWN = "Unknown"
    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"


def calculate_catalyst_strength(
    active_categories: list[CatalystCategory], freshness: CatalystFreshness
) -> CatalystStrength:
    """Calculate catalyst strength using active intelligence only."""

    if not active_categories:
        return CatalystStrength.WEAK

    category_count = len(active_categories)

    if freshness == CatalystFreshness.BREAKING and category_count >= 2:
        return CatalystStrength.STRONG

    if freshness == CatalystFreshness.BREAKING:
        return CatalystStrength.MODERATE

    if freshness == CatalystFreshness.FRESH and category_count >= 2:
        return CatalystStrength.STRONG

    if freshness == CatalystFreshness.FRESH:
        return CatalystStrength.MODERATE

    if freshness == CatalystFreshness.RECENT:
        return CatalystStrength.MODERATE

    return CatalystStrength.WEAK
