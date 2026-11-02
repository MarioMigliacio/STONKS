# =============================================================================
# File: research_runner.py
# Purpose: Coordinates historical research retrieval and result construction.
# =============================================================================

from stonks.cache.historical_cache_service import retrieve_daily_research_data
from stonks.cache.intraday_cache_service import retrieve_intraday_data
from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataStatus,
)
from stonks.models.research_data_retrieval import (
    ResearchDataRetrieval,
    ResearchRetrievalStatus,
)
from stonks.models.timeframe import Timeframe
from stonks.price_action.candle_aggregation import MINUTE_INTERVALS
from stonks.price_action.historical_research_service import (
    build_historical_research_result,
)


def _retrieve_source_candles(
    request: HistoricalResearchRequest,
) -> ResearchDataRetrieval:
    """Retrieve the lowest supported source interval for research."""
    if request.interval in MINUTE_INTERVALS:
        return retrieve_intraday_data(
            symbol=request.symbol,
            timeframe=Timeframe.ONE_MINUTE,
            start_date=request.start_date,
            end_date=request.end_date,
            force_refresh=request.force_refresh,
        )

    return retrieve_daily_research_data(
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        force_refresh=request.force_refresh,
    )


def run_historical_research(
    request: HistoricalResearchRequest,
) -> HistoricalResearchResult:
    """
    Execute a historical research request.

    Retrieval failures are represented as research results rather than
    being mistaken for successful empty market-data responses.
    """
    retrieval = _retrieve_source_candles(request)

    if retrieval.status == ResearchRetrievalStatus.SUCCESS:
        return build_historical_research_result(
            request=request,
            candles=retrieval.candles,
            data_source=retrieval.source,
        )

    if retrieval.status == ResearchRetrievalStatus.NO_DATA:
        status = ResearchDataStatus.UNAVAILABLE
    else:
        status = ResearchDataStatus.ERROR

    return HistoricalResearchResult(
        request=request,
        source_candles=[],
        display_candles=[],
        window_metrics=None,
        data_source=retrieval.source,
        status=status,
        message=retrieval.message or retrieval.status.value,
    )
