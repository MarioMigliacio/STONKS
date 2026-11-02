# =============================================================================
# File: test_historical_research_contracts.py
# Purpose: Tests historical research request and result contracts.
# =============================================================================

from datetime import date, datetime, timezone

import pytest

from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataSource,
    ResearchDataStatus,
)
from stonks.models.research_interval import ResearchInterval


def make_request(**overrides) -> HistoricalResearchRequest:
    """Create a valid request with optional parameter overrides."""
    values = {
        "symbol": "AMD",
        "start_date": date(2026, 9, 25),
        "end_date": date(2026, 9, 25),
        "interval": ResearchInterval.FIVE_MINUTES,
    }
    values.update(overrides)
    return HistoricalResearchRequest(**values)


def test_normalizes_symbol() -> None:
    """Tickers should be normalized before retrieval."""
    request = make_request(symbol=" amd ")

    assert request.symbol == "AMD"


def test_rejects_empty_symbol() -> None:
    """A research request must identify a ticker."""
    with pytest.raises(ValueError):
        make_request(symbol="   ")


def test_rejects_reversed_date_range() -> None:
    """Requested dates must be chronological."""
    with pytest.raises(ValueError):
        make_request(
            start_date=date(2026, 9, 26),
            end_date=date(2026, 9, 25),
        )


def test_rejects_multi_day_intraday_request() -> None:
    """Intraday research is limited to one trading date."""
    with pytest.raises(ValueError):
        make_request(end_date=date(2026, 9, 28))


def test_accepts_quarterly_research_range() -> None:
    """Calendar research may span multiple trading dates."""
    request = make_request(
        start_date=date(2025, 1, 1),
        end_date=date(2026, 9, 30),
        interval=ResearchInterval.QUARTERLY,
    )

    assert request.interval == ResearchInterval.QUARTERLY


def test_rejects_partial_analysis_window() -> None:
    """Analysis windows require both boundaries."""
    with pytest.raises(ValueError):
        make_request(window_start=datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc))


def test_rejects_naive_analysis_window() -> None:
    """Analysis boundaries must include timezone information."""
    with pytest.raises(ValueError):
        make_request(
            window_start=datetime(2026, 9, 25, 13, 30),
            window_end=datetime(2026, 9, 25, 14, 0),
        )


def test_accepts_valid_analysis_window() -> None:
    """A valid window should retain its requested boundaries."""
    start = datetime(2026, 9, 25, 13, 30, tzinfo=timezone.utc)
    end = datetime(2026, 9, 25, 14, 0, tzinfo=timezone.utc)

    request = make_request(window_start=start, window_end=end)

    assert request.window_start == start
    assert request.window_end == end


def test_result_preserves_source_and_display_separation() -> None:
    """The research result retains separate analysis and chart datasets."""
    request = make_request()

    result = HistoricalResearchResult(
        request=request,
        source_candles=[],
        display_candles=[],
        window_metrics=None,
        data_source=ResearchDataSource.CACHE,
        status=ResearchDataStatus.AVAILABLE,
    )

    assert result.source_candles is not result.display_candles
    assert result.data_source == ResearchDataSource.CACHE
    assert result.status == ResearchDataStatus.AVAILABLE
    assert result.incomplete_display_periods == 0
