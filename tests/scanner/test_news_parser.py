from datetime import timezone

from stonks.scanner.news_parser import parse_news_articles


def test_parse_news_articles_keeps_primary_ticker() -> None:
    """Keep an article when the requested ticker has highest relevance."""

    data = {
        "feed": [
            {
                "title": "Tesla Controls 59% of the U.S. EV Market",
                "source": "Yahoo Finance",
                "time_published": "20260821T222500",
                "summary": "Tesla market share increased.",
                "url": "https://example.com/tesla",
                "ticker_sentiment": [
                    {
                        "ticker": "TSLA",
                        "relevance_score": "1.000000",
                        "ticker_sentiment_score": "0.289720",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    },
                    {
                        "ticker": "NVDA",
                        "relevance_score": "0.601390",
                        "ticker_sentiment_score": "0.325885",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    },
                ],
            }
        ]
    }

    articles = parse_news_articles(
        data,
        "TSLA"
    )

    assert len(articles) == 1
    assert articles[0].title == (
        "Tesla Controls 59% of the U.S. EV Market"
    )
    assert articles[0].sentiment_score == 0.289720
    assert articles[0].sentiment_label == "Somewhat-Bullish"


def test_parse_news_articles_rejects_secondary_ticker() -> None:
    """Reject an article when the requested ticker is only secondary."""

    data = {
        "feed": [
            {
                "title": "Portfolio Design Labs Purchases Uber",
                "source": "MarketBeat",
                "time_published": "20260821T102242",
                "summary": (
                    "Uber expands robotaxi operations with Tesla mentioned "
                    "as a competitor."
                ),
                "url": "https://example.com/uber",
                "ticker_sentiment": [
                    {
                        "ticker": "UBER",
                        "relevance_score": "1.000000",
                        "ticker_sentiment_score": "0.255968",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    },
                    {
                        "ticker": "TSLA",
                        "relevance_score": "0.630476",
                        "ticker_sentiment_score": "-0.213266",
                        "ticker_sentiment_label": "Somewhat-Bearish",
                    },
                ],
            }
        ]
    }

    articles = parse_news_articles(
        data,
        "TSLA"
    )

    assert articles == []


def test_parse_news_articles_uses_ticker_specific_sentiment() -> None:
    """
    Use sentiment for the requested ticker instead of the
    article's overall sentiment.
    """

    data = {
        "feed": [
            {
                "title": "Tesla and Nvidia Discuss AI Expansion",
                "source": "Example News",
                "time_published": "20260821T120000",
                "summary": "Tesla discusses future AI investments.",
                "url": "https://example.com/tesla-ai",

                # Deliberately different from TSLA-specific sentiment.
                "overall_sentiment_score": "0.750000",
                "overall_sentiment_label": "Bullish",

                "ticker_sentiment": [
                    {
                        "ticker": "TSLA",
                        "relevance_score": "1.000000",
                        "ticker_sentiment_score": "-0.213266",
                        "ticker_sentiment_label": "Somewhat-Bearish",
                    },
                    {
                        "ticker": "NVDA",
                        "relevance_score": "0.500000",
                        "ticker_sentiment_score": "0.400000",
                        "ticker_sentiment_label": "Bullish",
                    },
                ],
            }
        ]
    }

    articles = parse_news_articles(
        data,
        "TSLA"
    )

    assert len(articles) == 1

    article = articles[0]

    assert article.sentiment_score == -0.213266
    assert article.sentiment_label == "Somewhat-Bearish"


def test_parse_news_articles_creates_utc_timestamp() -> None:
    """Parse Alpha Vantage publication times as timezone-aware UTC."""

    data = {
        "feed": [
            {
                "title": "Tesla Announces New Development",
                "source": "Example News",
                "time_published": "20260821T222500",
                "summary": "Tesla announces a new development.",
                "url": "https://example.com/tesla-development",
                "ticker_sentiment": [
                    {
                        "ticker": "TSLA",
                        "relevance_score": "1.000000",
                        "ticker_sentiment_score": "0.300000",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    }
                ],
            }
        ]
    }

    articles = parse_news_articles(
        data,
        "TSLA"
    )

    assert len(articles) == 1

    published_at = articles[0].published_at

    assert published_at.year == 2026
    assert published_at.month == 8
    assert published_at.day == 21
    assert published_at.hour == 22
    assert published_at.minute == 25
    assert published_at.tzinfo == timezone.utc


def test_parse_news_articles_skips_missing_publication_time() -> None:
    """Skip articles that do not contain a publication timestamp."""

    data = {
        "feed": [
            {
                "title": "Tesla Article Without Time",
                "source": "Example News",
                "summary": "This article has no publication time.",
                "url": "https://example.com/no-time",
                "ticker_sentiment": [
                    {
                        "ticker": "TSLA",
                        "relevance_score": "1.000000",
                        "ticker_sentiment_score": "0.200000",
                        "ticker_sentiment_label": "Somewhat-Bullish",
                    }
                ],
            }
        ]
    }

    articles = parse_news_articles(
        data,
        "TSLA"
    )

    assert articles == []


def test_parse_news_articles_returns_empty_when_feed_missing() -> None:
    """Return no articles when the provider response has no news feed."""

    articles = parse_news_articles(
        {},
        "TSLA"
    )

    assert articles == []