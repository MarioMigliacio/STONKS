# =============================================================================
# File: historical_volume_data.py
# Purpose: Defines normalized historical volume data used by scanner metrics.
#
# Notes:
# - This model represents one daily historical volume record.
# - It is derived from cached provider data.
# - Relative Volume calculations will use collections of these records.
# =============================================================================

from dataclasses import dataclass


@dataclass
class HistoricalVolumeData:
    """
    Represents one day of historical volume data.

    Attributes:
        trade_date:
            Trading date for the historical record.

        volume:
            Total trading volume for that date.
    """

    trade_date: str
    volume: int
