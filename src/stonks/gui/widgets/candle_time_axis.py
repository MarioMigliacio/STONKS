# =============================================================================
# File: candle_time_axis.py
# Purpose: Formats evenly spaced candle positions using market timestamps.
# =============================================================================

from datetime import datetime
from typing import List

import pyqtgraph as pg


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

    def tickStrings(self, values: List[float], scale: float, spacing: float) -> List[str]:
        """Format visible candle indices without implying elapsed-time spacing."""
        del scale, spacing
        labels = []
        for value in values:
            index = round(value)
            if abs(value - index) > 0.001 or not 0 <= index < len(self.m_timestamps):
                labels.append("")
                continue
            timestamp = self.m_timestamps[index]
            labels.append(self._format_timestamp(timestamp))
        return labels

    def _format_timestamp(self, timestamp: datetime) -> str:
        """Show dates for multi-day data and clock times within one day."""
        if not self.m_timestamps:
            return ""
        if self.m_timestamps[0].date() == self.m_timestamps[-1].date():
            return timestamp.strftime("%H:%M")
        return timestamp.strftime("%b %d")
