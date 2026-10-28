# =============================================================================
# File: cia_analysis_service.py
# Purpose: Coordinates news retrieval and catalyst analysis independently of UI.
# =============================================================================

from datetime import datetime, timezone
from typing import Callable, Optional

from stonks.api.market_data import get_news_sentiment
from stonks.cia.cia_analysis_result import CiaAnalysisResult
from stonks.cia.cia_engine import build_catalyst_report
from stonks.cia.duplicate_filter import filter_duplicate_articles
from stonks.scanner.news_parser import parse_news_articles


class CiaAnalysisService:
    """Coordinate provider news retrieval and deterministic catalyst analysis.

    Attributes:
        m_news_fetcher:
            Callable accepting a ticker and article limit and returning a
            provider response, allowing tests to avoid network access.
    """

    def __init__(self, news_fetcher: Optional[Callable] = None) -> None:
        """Initialize the service with an optional injectable news provider.

        Args:
            news_fetcher:
                Optional replacement for the Alpha Vantage news function.
        """
        self.m_news_fetcher = news_fetcher if news_fetcher is not None else get_news_sentiment

    def analyze(self, ticker: str, limit: int = 50) -> CiaAnalysisResult:
        """Retrieve, normalize, deduplicate, and analyze ticker news.

        Args:
            ticker:
                Stock symbol to investigate; whitespace is stripped.
            limit:
                Maximum number of articles requested from the provider.

        Returns:
            CiaAnalysisResult containing the report and supporting articles.
            A valid empty feed produces an empty report and article list.

        Raises:
            ValueError:
                If ticker is blank or the article limit is not positive.
            RuntimeError:
                If the provider fails or returns an invalid/error response.
        """
        symbol = ticker.strip().upper()

        if not symbol:
            raise ValueError("Ticker cannot be empty.")
        if limit < 1:
            raise ValueError("News article limit must be positive.")

        data = self.m_news_fetcher(symbol=symbol, limit=limit)

        if not isinstance(data, dict):
            raise RuntimeError("News provider did not return a valid response.")

        for key in ("Error Message", "Information", "Note"):
            if data.get(key):
                raise RuntimeError(f"News provider: {data[key]}")

        if not isinstance(data.get("feed"), list):
            raise RuntimeError("News provider response is missing a valid feed.")

        articles = parse_news_articles(data, symbol)
        unique_articles = filter_duplicate_articles(articles)
        report = build_catalyst_report(
            ticker=symbol,
            articles=unique_articles,
            original_article_count=len(articles),
            current_time=datetime.now(timezone.utc),
        )
        return CiaAnalysisResult(report=report, articles=unique_articles)
