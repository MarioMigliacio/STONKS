# =============================================================================
# File: test_research_data_retrieval.py
# Purpose: Tests the research data retrieval outcome contract.
# =============================================================================

from datetime import datetime, timezone

import pytest

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_result import ResearchDataSource
from stonks.models.research_data_retrieval import (
    ResearchDataRetrieval,
    ResearchRetrievalStatus,
)


def make_candle() -> CandleData:
    """Create one valid normalized candle."""
    return CandleData(
        timestamp=datetime(2026, 9, 28, tzinfo=timezone.utc),
        open_price=100.0,
        high_price=105.0,
        low_price=98.0,
        close_price=103.0,
        volume=1000,
    )


@pytest.mark.parametrize(
    "source",
    [
        ResearchDataSource.CACHE,
        ResearchDataSource.PROVIDER,
    ],
)
def test_successful_retrieval(source: ResearchDataSource) -> None:
    """Successful retrieval should preserve data provenance."""
    candle = make_candle()

    result = ResearchDataRetrieval(
        candles=[candle],
        status=ResearchRetrievalStatus.SUCCESS,
        source=source,
    )

    assert result.candles == [candle]
    assert result.source == source
    assert result.status == ResearchRetrievalStatus.SUCCESS


@pytest.mark.parametrize(
    "status",
    [
        ResearchRetrievalStatus.NO_DATA,
        ResearchRetrievalStatus.API_DISABLED,
        ResearchRetrievalStatus.PROVIDER_ERROR,
    ],
)
def test_unsuccessful_retrieval(status: ResearchRetrievalStatus) -> None:
    """Unsuccessful retrieval should support empty data."""
    result = ResearchDataRetrieval(
        candles=[],
        status=status,
        message="Data unavailable.",
    )

    assert result.candles == []
    assert result.status == status


def test_success_requires_candles() -> None:
    """A successful result cannot be empty."""
    with pytest.raises(ValueError):
        ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.SUCCESS,
            source=ResearchDataSource.CACHE,
        )


def test_success_requires_provenance() -> None:
    """A successful result must identify its data source."""
    with pytest.raises(ValueError):
        ResearchDataRetrieval(
            candles=[make_candle()],
            status=ResearchRetrievalStatus.SUCCESS,
        )


def test_failure_cannot_contain_candles() -> None:
    """A failed retrieval cannot claim to contain valid data."""
    with pytest.raises(ValueError):
        ResearchDataRetrieval(
            candles=[make_candle()],
            status=ResearchRetrievalStatus.PROVIDER_ERROR,
        )


def test_api_disabled_cannot_claim_data_source() -> None:
    """Disabled API access is not a cache or provider response."""
    with pytest.raises(ValueError):
        ResearchDataRetrieval(
            candles=[],
            status=ResearchRetrievalStatus.API_DISABLED,
            source=ResearchDataSource.PROVIDER,
        )
