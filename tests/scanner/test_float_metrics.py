# =============================================================================
# File: test_float_metrics.py
# Purpose: Pytest file for float_metrics.py.
# =============================================================================

from stonks.scanner.float_metrics import calculate_float_turnover


def test_calculate_float_turnover():
    """Verify volume is calculated relative to reported public float."""

    result = calculate_float_turnover(
        volume=5_000_000,
        float_shares=10_000_000,
    )

    assert result == 0.5


def test_calculate_float_turnover_returns_none_for_zero_float():
    """Verify zero float does not cause division by zero."""

    result = calculate_float_turnover(
        volume=5_000_000,
        float_shares=0,
    )

    assert result is None


def test_calculate_float_turnover_returns_none_for_negative_float():
    """Verify invalid negative float values are rejected."""

    result = calculate_float_turnover(
        volume=5_000_000,
        float_shares=-1,
    )

    assert result is None
