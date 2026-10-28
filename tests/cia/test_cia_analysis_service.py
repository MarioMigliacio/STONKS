# =============================================================================
# File: test_cia_analysis_service.py
# Purpose: Tests provider-independent CIA analysis without network access.
# =============================================================================

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from stonks.api.exceptions import ProviderAccessError
from stonks.cia.cia_analysis_service import CiaAnalysisService
from stonks.models.news_article import NewsArticle


def _article(title: str, url: str) -> NewsArticle:
    return NewsArticle(
        title=title,
        source="Example News",
        published_at=datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc),
        summary="Quarterly earnings were announced.",
        url=url,
        sentiment_score=0.4,
        sentiment_label="Bullish",
    )


def test_analyze_returns_report_and_deduplicated_articles() -> None:
    provider = Mock()
    provider.get_news.return_value = [
        _article("NVDA earnings", "https://example.com/a"),
        _article("NVDA earnings", "https://example.com/b"),
        _article("NVDA quarterly results", "https://example.com/c"),
    ]

    result = CiaAnalysisService(provider).analyze(" nvda ")

    provider.get_news.assert_called_once_with(symbol="NVDA", limit=50)
    assert result.report.ticker == "NVDA"
    assert result.report.original_article_count == 3
    assert result.report.unique_article_count == 2
    assert result.report.duplicate_articles_removed == 1
    assert len(result.articles) == 2


def test_empty_feed_returns_empty_analysis() -> None:
    provider = Mock()
    provider.get_news.return_value = []
    result = CiaAnalysisService(provider).analyze("NVDA")
    assert result.articles == []
    assert result.report.original_article_count == 0
    assert result.report.unique_article_count == 0


@pytest.mark.parametrize("ticker,limit", [("", 50), ("  ", 50), ("NVDA", 0)])
def test_invalid_input_is_rejected_without_fetch(ticker: str, limit: int) -> None:
    provider = Mock()
    with pytest.raises(ValueError):
        CiaAnalysisService(provider).analyze(ticker, limit=limit)
    provider.get_news.assert_not_called()


def test_provider_failure_propagates() -> None:
    provider = Mock()
    provider.get_news.side_effect = ProviderAccessError("Premium endpoint")
    with pytest.raises(ProviderAccessError, match="Premium endpoint"):
        CiaAnalysisService(provider).analyze("NVDA")
