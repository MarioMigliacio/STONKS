# =============================================================================
# File: test_float_classification.py
# Purpose: Pytest file for test_float_classification.py.
# =============================================================================

from stonks.scanner.float_classification import (
    FloatClassification,
    classify_float_size,
)


def test_classify_float_size_returns_unknown_for_zero_float():
    """Verify zero float is classified as unknown."""

    result = classify_float_size(0)

    assert result == FloatClassification.UNKNOWN


def test_classify_float_size_returns_unknown_for_negative_float():
    """Verify negative float is classified as unknown."""

    result = classify_float_size(-1)

    assert result == FloatClassification.UNKNOWN


def test_classify_float_size_returns_very_low():
    """Verify float below five million shares is classified as very low."""

    result = classify_float_size(4_999_999)

    assert result == FloatClassification.VERY_LOW


def test_classify_float_size_returns_low():
    """Verify float from five to ten million shares is classified as low."""

    result = classify_float_size(7_500_000)

    assert result == FloatClassification.LOW


def test_classify_float_size_returns_medium():
    """Verify float from ten to fifty million shares is classified as medium."""

    result = classify_float_size(25_000_000)

    assert result == FloatClassification.MEDIUM


def test_classify_float_size_returns_high():
    """Verify float of fifty million shares or more is classified as high."""

    result = classify_float_size(50_000_000)

    assert result == FloatClassification.HIGH
