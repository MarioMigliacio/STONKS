# =============================================================================
# File: historical_research_service.py
# Purpose: Builds historical research results from normalized source candles.
# =============================================================================

from datetime import datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataSource,
    ResearchDataStatus,
    ResearchWindowMetrics,
)
from stonks.models.market_session import MarketSession
from stonks.models.price_action_data import PriceActionData
from stonks.models.research_interval import ResearchInterval
from stonks.price_action.candle_aggregation import (
    MINUTE_INTERVALS,
    aggregate_candles,
)
from stonks.price_action.candle_window import select_candle_window

EASTERN = ZoneInfo("America/New_York")

SESSION_BOUNDARIES = {
    MarketSession.PRE_MARKET: (time(4, 0), time(9, 30)),
    MarketSession.REGULAR: (time(9, 30), time(16, 0)),
    MarketSession.AFTER_HOURS: (time(16, 0), time(20, 0)),
}


def _filter_source_candles(
    request: HistoricalResearchRequest,
    candles: list[CandleData],
    intraday: bool,
) -> list[CandleData]:
    """Select candles matching the research dates and market session."""
    filtered = []

    for candle in candles:
        timestamp = candle.timestamp

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Source candle timestamps must be timezone-aware.")

        if intraday:
            eastern = timestamp.astimezone(EASTERN)
            trading_date = eastern.date()

            if trading_date != request.start_date:
                continue

            if request.session is not None:
                start, end = SESSION_BOUNDARIES[request.session]

                if not start <= eastern.time().replace(tzinfo=None) < end:
                    continue
        else:
            # Daily candles use the UTC-midnight trading-date convention.
            trading_date = timestamp.astimezone(timezone.utc).date()

            if not request.start_date <= trading_date <= request.end_date:
                continue

        filtered.append(candle)

    return sorted(filtered, key=lambda item: item.timestamp)


def _calculate_window_metrics(
    candles: list[CandleData],
    start_time: datetime,
    end_time: datetime,
) -> Optional[ResearchWindowMetrics]:
    """Calculate OHLCV metrics using the selected source candles."""
    selected = select_candle_window(candles, start_time, end_time)

    if not selected:
        return None

    first = selected[0]
    last = selected[-1]

    high = max(candle.high_price for candle in selected)
    low = min(candle.low_price for candle in selected)

    change = (last.close_price - first.open_price) / first.open_price * 100 if first.open_price > 0 else None

    price_range = (high - low) / low * 100 if low > 0 else None

    return ResearchWindowMetrics(
        start_time=start_time,
        end_time=end_time,
        price_action=PriceActionData(
            change_percent=change,
            high_price=high,
            low_price=low,
            range_percent=price_range,
        ),
        volume=sum(candle.volume for candle in selected),
        candle_count=len(selected),
    )


def build_historical_research_result(
    request: HistoricalResearchRequest,
    candles: list[CandleData],
    data_source: Optional[ResearchDataSource] = None,
) -> HistoricalResearchResult:
    """
    Build a historical research result from normalized source candles.

    Args:
        request:
            Validated research parameters.

        candles:
            One-minute or daily normalized source candles.

        data_source:
            Provenance determined by the data retrieval layer.

    Returns:
        Chart candles, optional analysis metrics, and availability status.
    """
    intraday = request.interval in MINUTE_INTERVALS

    source_interval = ResearchInterval.ONE_MINUTE if intraday else ResearchInterval.DAILY

    source_candles = _filter_source_candles(
        request,
        candles,
        intraday,
    )

    if not source_candles:
        return HistoricalResearchResult(
            request=request,
            source_candles=[],
            display_candles=[],
            window_metrics=None,
            data_source=data_source,
            status=ResearchDataStatus.UNAVAILABLE,
            message="No historical candles match the requested period.",
        )

    aggregated = aggregate_candles(
        source_candles,
        request.interval,
        source_interval,
    )

    display_candles = [item.candle for item in aggregated]

    incomplete_periods = sum(item.has_missing_source_candles for item in aggregated)

    window_metrics = None

    if request.window_start is not None and request.window_end is not None:
        window_metrics = _calculate_window_metrics(
            source_candles,
            request.window_start,
            request.window_end,
        )

    status = ResearchDataStatus.PARTIAL if incomplete_periods else ResearchDataStatus.AVAILABLE

    message = None

    if incomplete_periods:
        message = f"{incomplete_periods} display period(s) have fewer source candles than expected."

    return HistoricalResearchResult(
        request=request,
        source_candles=source_candles,
        display_candles=display_candles,
        window_metrics=window_metrics,
        data_source=data_source,
        status=status,
        message=message,
        incomplete_display_periods=incomplete_periods,
    )
