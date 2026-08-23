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