# =============================================================================
# File: float_classification.py
# Purpose: Classifies reported public float by share count.
# =============================================================================

from enum import Enum


class FloatClassification(Enum):
    """Represents a scanner-friendly public-float size classification."""

    UNKNOWN = "Unknown"
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


def classify_float_size(
    float_shares: int,
) -> FloatClassification:
    """Classify reported public float by share count."""

    if float_shares <= 0:
        return FloatClassification.UNKNOWN

    if float_shares < 5_000_000:
        return FloatClassification.VERY_LOW

    if float_shares < 10_000_000:
        return FloatClassification.LOW

    if float_shares < 50_000_000:
        return FloatClassification.MEDIUM

    return FloatClassification.HIGH
