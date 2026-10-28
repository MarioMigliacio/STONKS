# =============================================================================
# File: test_cia_analysis_service.py
# Purpose: Verifies CIA service orchestration without external API requests.
# =============================================================================

from unittest.mock import Mock

import pytest

from stonks.cia.cia_analysis_service import CiaAnalysisService


def _article(title, url):
    return {
        "title": title,
        "source": "Example News",
        "summary": "Quarterly earnings were announced.",
        "url": url,
        "time_published": "20261026T120000",
        "ticker_sentiment": [
            {
                "ticker": "NVDA",
                "relevance_score": "0.95",
                "ticker_sentiment_score": "0.40",
                "ticker_sentiment_label": "Bullish",
            }
        ],
    }


def test_analyze_returns_report_and_deduplicated_articles():
    fetcher = Mock(
        return_value={
            "feed": [
                _article("NVDA earnings", "https://example.com/a"),
                _article("NVDA earnings", "https://example.com/b"),
                _article("NVDA quarterly results", "https://example.com/c"),
            ]
        }
    )

    result = CiaAnalysisService(fetcher).analyze(" nvda ")

    fetcher.assert_called_once_with(symbol="NVDA", limit=50)
    assert result.report.ticker == "NVDA"
    assert result.report.original_article_count == 3
    assert result.report.unique_article_count == 2
    assert result.report.duplicate_articles_removed == 1
    assert len(result.articles) == 2


def test_empty_feed_returns_empty_analysis():
    result = CiaAnalysisService(Mock(return_value={"feed": []})).analyze("NVDA")
    assert result.articles == []
    assert result.report.original_article_count == 0
    assert result.report.unique_article_count == 0


@pytest.mark.parametrize("ticker,limit", [("", 50), ("  ", 50), ("NVDA", 0)])
def test_invalid_input_is_rejected_without_fetch(ticker, limit):
    fetcher = Mock()
    with pytest.raises(ValueError):
        CiaAnalysisService(fetcher).analyze(ticker, limit=limit)
    fetcher.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [None, {}, {"Note": "Rate limit"}, {"Information": "API limit"}, {"Error Message": "Bad symbol"}, {"feed": {}}],
)
def test_provider_failure_is_not_misreported_as_empty_news(response):
    with pytest.raises(RuntimeError):
        CiaAnalysisService(Mock(return_value=response)).analyze("NVDA")
