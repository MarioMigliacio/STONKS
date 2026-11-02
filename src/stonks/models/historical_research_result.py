# =============================================================================
# File: historical_research_result.py
# Purpose: Represents historical research data and analysis results.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.price_action_data import PriceActionData


class ResearchDataSource(Enum):
    """Identifies where the research data was obtained."""

    CACHE = "cache"
    PROVIDER = "provider"


class ResearchDataStatus(Enum):
    """Describes the availability of historical research data."""

    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class ResearchWindowMetrics:
    """
    Represents calculated metrics for a selected analysis window.

    Attributes:
        start_time:
            Inclusive start of the analyzed window.

        end_time:
            Exclusive end of the analyzed window.

        price_action:
            Calculated change, high, low, and range.

        volume:
            Total volume across selected source candles.

        candle_count:
            Number of source candles included.
    """

    start_time: datetime
    end_time: datetime
    price_action: PriceActionData
    volume: int
    candle_count: int


@dataclass(frozen=True)
class HistoricalResearchResult:
    """
    Represents the output of a historical research operation.

    Attributes:
        request:
            Original normalized research request.

        source_candles:
            Normalized candles used for analysis.

        display_candles:
            Aggregated candles used by the chart.

        window_metrics:
            Metrics for the selected analysis window, if available.

        data_source:
            Cache or provider provenance, when known.

        status:
            Availability or failure classification.

        message:
            Optional user-facing explanation.

        incomplete_display_periods:
            Number of display buckets with detected missing source candles.
    """

    request: HistoricalResearchRequest
    source_candles: list[CandleData]
    display_candles: list[CandleData]
    window_metrics: Optional[ResearchWindowMetrics]
    data_source: Optional[ResearchDataSource]
    status: ResearchDataStatus
    message: Optional[str] = None
    incomplete_display_periods: int = 0
