# =============================================================================
# File: cia_analysis_service.py
# Purpose: Coordinates provider-independent news retrieval and CIA analysis.
# =============================================================================

from datetime import datetime, timezone

from stonks.api.providers.news_provider import NewsProvider
from stonks.cia.cia_analysis_result import CiaAnalysisResult
from stonks.cia.cia_engine import build_catalyst_report
from stonks.cia.duplicate_filter import filter_duplicate_articles


class CiaAnalysisService:
    """Coordinate news retrieval and deterministic catalyst analysis.

    Attributes:
        m_news_provider:
            Provider supplying normalized ticker-specific news articles.
    """

    def __init__(self, news_provider: NewsProvider) -> None:
        """Initialize with an explicitly selected news provider."""
        self.m_news_provider = news_provider

    def analyze(self, ticker: str, limit: int = 50) -> CiaAnalysisResult:
        """Analyze normalized news for a ticker and return supporting articles.

        A successful empty feed produces an empty report. Provider errors
        propagate unchanged so callers can display the actual failure.
        """
        symbol = ticker.strip().upper()

        if not symbol:
            raise ValueError("Ticker cannot be empty.")
        if limit < 1:
            raise ValueError("News article limit must be positive.")

        articles = self.m_news_provider.get_news(symbol=symbol, limit=limit)
        unique_articles = filter_duplicate_articles(articles)
        report = build_catalyst_report(
            ticker=symbol,
            articles=unique_articles,
            original_article_count=len(articles),
            current_time=datetime.now(timezone.utc),
        )

        return CiaAnalysisResult(report=report, articles=unique_articles)
