# =============================================================================
# File: research_data_retrieval.py
# Purpose: Represents the outcome of research market-data retrieval.
# =============================================================================

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from stonks.models.candle_data import CandleData
from stonks.models.historical_research_result import ResearchDataSource


class ResearchRetrievalStatus(Enum):
    """Describes the outcome of a market-data retrieval attempt."""

    SUCCESS = "success"
    NO_DATA = "no_data"
    API_DISABLED = "api_disabled"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True)
class ResearchDataRetrieval:
    """
    Represents retrieved market data and its retrieval outcome.

    Attributes:
        candles:
            Normalized source candles returned by retrieval.

        status:
            Outcome of the retrieval attempt.

        source:
            Cache or provider provenance, when known.

        message:
            Optional explanation of the retrieval outcome.
    """

    candles: list[CandleData]
    status: ResearchRetrievalStatus
    source: Optional[ResearchDataSource] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate consistency between retrieval status and data."""
        if self.status == ResearchRetrievalStatus.SUCCESS:
            if not self.candles:
                raise ValueError("Successful retrieval requires source candles.")

            if self.source is None:
                raise ValueError("Successful retrieval requires data provenance.")

        elif self.candles:
            raise ValueError("Unsuccessful retrieval cannot contain source candles.")

        if self.status == ResearchRetrievalStatus.API_DISABLED and self.source is not None:
            raise ValueError("API-disabled retrieval cannot have a data source.")
