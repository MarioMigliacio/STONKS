# =============================================================================
# File: news_parser.py
# Purpose: Normalizes provider news responses into NewsArticle models.
# =============================================================================

from stonks.models.news_article import NewsArticle
from datetime import datetime

def parse_published_time(value: str) -> datetime:
    """Convert an Alpha Vantage timestamp into a datetime object."""

    return datetime.strptime(
        value,
        "%Y%m%dT%H%M%S"
    )

def parse_news_articles(data) -> list[NewsArticle]:
    """Parse Alpha Vantage news data into normalized article models."""

    if not data:
        return []

    feed = data.get("feed")

    if not feed:
        return []

    articles = []

    for article_data in feed:
        sentiment_score = float(
            article_data.get(
                "overall_sentiment_score",
                0.0
            )
        )

        published_time = article_data.get(
            "time_published",
            ""
        )

        if not published_time:
            continue

        articles.append(
            NewsArticle(
                title=article_data.get("title", ""),
                source=article_data.get("source", ""),
                published_at=parse_published_time(
                    published_time
                ),
                summary=article_data.get("summary", ""),
                url=article_data.get("url", ""),
                overall_sentiment_score=sentiment_score,
                overall_sentiment_label=article_data.get(
                    "overall_sentiment_label",
                    ""
                )
            )
        )

    return articles