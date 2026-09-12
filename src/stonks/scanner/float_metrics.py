# =============================================================================
# File: float_metrics.py
# Purpose: Provides calculations for scanner metrics derived from public-float data.
# =============================================================================

from typing import Optional


def calculate_float_turnover(
    volume: int,
    float_shares: int,
) -> Optional[float]:
    """Calculate trading volume relative to reported public float."""

    if float_shares <= 0:
        return None

    return volume / float_shares
