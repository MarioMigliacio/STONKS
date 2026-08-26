# =============================================================================
# File: relative_volume.py
# Purpose: Provides Relative Volume calculations for scanner metrics.
#
# Notes:
# - Relative Volume compares current volume against average historical volume.
# - Historical data should come from the cache layer whenever possible.
# =============================================================================

from stonks.models.historical_volume_data import HistoricalVolumeData


def calculate_average_volume(
    historical_volumes: list[HistoricalVolumeData],
    lookback_days: int,
    excluded_trade_date: str = "",
) -> float:
    """Calculate average volume over a lookback window."""

    if not historical_volumes:
        return 0.0

    filtered_volumes = [
        historical_volume
        for historical_volume in historical_volumes
        if historical_volume.trade_date != excluded_trade_date
    ]

    volumes = [historical_volume.volume for historical_volume in filtered_volumes[:lookback_days]]

    if not volumes:
        return 0.0

    return sum(volumes) / len(volumes)


def calculate_relative_volume(current_volume: int, average_volume: float) -> float:
    """Calculate relative volume."""

    if average_volume == 0:
        return 0.0

    return current_volume / average_volume
