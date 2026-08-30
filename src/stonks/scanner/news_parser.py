# =============================================================================
# File: news_parser.py
# Purpose: Normalizes provider news responses into NewsArticle models.
# =============================================================================

import logging
from datetime import datetime, timezone

from stonks.models.news_article import NewsArticle

logger = logging.getLogger(__name__)


def parse_published_time(value: str) -> datetime:
    """Convert an Alpha Vantage UTC timestamp into a datetime object."""

    parsed_time = datetime.strptime(value, "%Y%m%dT%H%M%S")

    return parsed_time.replace(tzinfo=timezone.utc)


def parse_news_articles(data, symbol: str) -> list[NewsArticle]:
    """Parse ticker-relevant Alpha Vantage news into normalized articles."""

    if not data:
        return []

    feed = data.get("feed")

    if not feed:
        return []

    symbol = symbol.upper()

    articles: list[NewsArticle] = []

    for article_data in feed:
        published_time = article_data.get("time_published", "")

        if not published_time:
            continue

        ticker_sentiments = article_data.get("ticker_sentiment", [])

        if not ticker_sentiments:
            continue

        target_ticker_data = None

        for ticker_data in ticker_sentiments:
            if ticker_data.get("ticker", "").upper() == symbol:
                target_ticker_data = ticker_data
                break

        if not target_ticker_data:
            continue

        target_relevance = float(target_ticker_data.get("relevance_score", 0.0))

        highest_relevance = max(float(ticker_data.get("relevance_score", 0.0)) for ticker_data in ticker_sentiments)

        if target_relevance < highest_relevance:
            continue

        sentiment_score = float(target_ticker_data.get("ticker_sentiment_score", 0.0))

        sentiment_label = target_ticker_data.get("ticker_sentiment_label", "")

        articles.append(
            NewsArticle(
                title=article_data.get("title", ""),
                source=article_data.get("source", ""),
                published_at=parse_published_time(published_time),
                summary=article_data.get("summary", ""),
                url=article_data.get("url", ""),
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
            )
        )

    logger.debug("Parsed %d relevant news articles for %s from %d feed entries", len(articles), symbol, len(feed))

    return articles
