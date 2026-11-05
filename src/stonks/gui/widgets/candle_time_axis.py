# =============================================================================
# File: candle_time_axis.py
# Purpose: Formats evenly spaced candle positions using market timestamps.
# =============================================================================

from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

import pyqtgraph as pg

MARKET_TIMEZONE = ZoneInfo("America/New_York")


class CandleTimeAxis(pg.AxisItem):
    """Label consecutive candle indices with their actual timestamps.

    Attributes:
        m_timestamps:
            Snapshot of timestamps corresponding to candle positions.
    """

    def __init__(self) -> None:
        """Create a bottom-oriented time axis."""
        super().__init__(orientation="bottom")
        self.m_timestamps: List[datetime] = []

    def set_timestamps(self, timestamps: List[datetime]) -> None:
        """Replace the timestamp lookup and refresh axis labels."""
        self.m_timestamps = list(timestamps)
        self.picture = None
        self.update()

    @staticmethod
    def market_time(timestamp: datetime) -> datetime:
        """Convert timezone-aware candle timestamps to New York market time."""
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Candle timestamps must be timezone-aware.")
        return timestamp.astimezone(MARKET_TIMEZONE)

    def tickStrings(
        self,
        values: List[float],
        scale: float,
        spacing: float,
    ) -> List[str]:
        """Format visible candle ticks using the local date range."""
        market_timestamps = [self.market_time(ts) for ts in self.m_timestamps]
        del scale, spacing

        indices = [
            round(value)
            for value in values
            if abs(value - round(value)) <= 0.001 and 0 <= round(value) < len(market_timestamps)
        ]

        if not indices:
            return [""] * len(values)

        visible_dates = {market_timestamps[index].date() for index in indices}

        time_format = "%H:%M" if len(visible_dates) == 1 else "%b %d"

        labels = []
        for value in values:
            index = round(value)

            if abs(value - index) > 0.001 or not 0 <= index < len(market_timestamps):
                labels.append("")
                continue

            labels.append(market_timestamps[index].strftime(time_format))

        return labels
