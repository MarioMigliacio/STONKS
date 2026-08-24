# =============================================================================
# File: test_duplicate_filter.py
# Purpose: Pytest file for duplicate_filter.py.
# =============================================================================

from datetime import datetime
from datetime import timezone

from stonks.cia.duplicate_filter import filter_duplicate_articles
from stonks.models.news_article import NewsArticle


def create_article(
    title: str,
    url: str
) -> NewsArticle:
    """Create a minimal NewsArticle for duplicate-filter tests."""

    return NewsArticle(
        title=title,
        source="Test Source",
        published_at=datetime(
            2026,
            8,
            23,
            tzinfo=timezone.utc
        ),
        summary="Test article summary.",
        url=url,
        sentiment_score=0.0,
        sentiment_label="Neutral"
    )


def test_filter_duplicate_articles_removes_matching_titles() -> None:
    """Remove articles with the same normalized title."""

    articles = [
        create_article(
            "Tesla Announces New Product",
            "https://example.com/article-1"
        ),
        create_article(
            "  tesla announces new product  ",
            "https://example.com/article-2"
        )
    ]

    unique_articles = filter_duplicate_articles(
        articles
    )

    assert len(unique_articles) == 1
    assert unique_articles[0].url == "https://example.com/article-1"


def test_filter_duplicate_articles_removes_matching_urls() -> None:
    """Remove articles that share the same URL."""

    articles = [
        create_article(
            "Tesla Announces New Product",
            "https://example.com/tesla"
        ),
        create_article(
            "Another Tesla Headline",
            "https://example.com/tesla"
        )
    ]

    unique_articles = filter_duplicate_articles(
        articles
    )

    assert len(unique_articles) == 1
    assert unique_articles[0].title == "Tesla Announces New Product"


def test_filter_duplicate_articles_keeps_empty_urls() -> None:
    """Do not treat missing URLs as duplicate identifiers."""

    articles = [
        create_article(
            "Tesla Article One",
            ""
        ),
        create_article(
            "Tesla Article Two",
            ""
        )
    ]

    unique_articles = filter_duplicate_articles(
        articles
    )

    assert len(unique_articles) == 2


def test_filter_duplicate_articles_keeps_unique_articles() -> None:
    """Keep articles with unique titles and URLs."""

    articles = [
        create_article(
            "Tesla Announces New Product",
            "https://example.com/article-1"
        ),
        create_article(
            "Tesla Expands Robotaxi Service",
            "https://example.com/article-2"
        ),
        create_article(
            "Tesla Reports Quarterly Earnings",
            "https://example.com/article-3"
        )
    ]

    unique_articles = filter_duplicate_articles(
        articles
    )

    assert len(unique_articles) == 3