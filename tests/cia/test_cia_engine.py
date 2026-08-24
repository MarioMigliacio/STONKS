# =============================================================================
# File: test_cia_engine.py
# Purpose: Pytest file for cia_engine.py.
# =============================================================================

from datetime import datetime, timedelta, timezone

import pytest

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_freshness import CatalystFreshness
from stonks.cia.catalyst_strength import CatalystStrength
from stonks.cia.cia_engine import build_catalyst_report, classify_overall_sentiment
from stonks.models.news_article import NewsArticle


def create_article(title: str, published_at: datetime, sentiment_score: float = 0.0) -> NewsArticle:
    """Create a minimal NewsArticle for C.I.A. engine tests."""

    return NewsArticle(
        title=title,
        source="Test Source",
        published_at=published_at,
        summary="Test article summary.",
        url="https://example.com/article",
        sentiment_score=sentiment_score,
        sentiment_label="Neutral",
    )


@pytest.mark.parametrize(
    "average_sentiment, expected_label",
    [
        (0.35, "Bullish"),
        (0.34, "Somewhat-Bullish"),
        (0.15, "Somewhat-Bullish"),
        (0.14, "Neutral"),
        (0.0, "Neutral"),
        (-0.14, "Neutral"),
        (-0.15, "Somewhat-Bearish"),
        (-0.34, "Somewhat-Bearish"),
        (-0.35, "Bearish"),
    ],
)
def test_classify_overall_sentiment_boundaries(average_sentiment: float, expected_label: str) -> None:
    """Classify sentiment correctly at and around configured boundaries."""

    overall_sentiment = classify_overall_sentiment(average_sentiment)

    assert overall_sentiment == expected_label


def test_build_catalyst_report_with_no_articles() -> None:
    """Build a sensible default report when no articles exist."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    report = build_catalyst_report(ticker="TSLA", articles=[], original_article_count=0, current_time=current_time)

    assert report.ticker == "TSLA"
    assert report.catalyst_strength == CatalystStrength.WEAK
    assert report.categories == []
    assert report.historical_categories == []
    assert report.average_sentiment == 0.0
    assert report.overall_sentiment == "Neutral"
    assert report.confidence == 0.0
    assert report.original_article_count == 0
    assert report.unique_article_count == 0
    assert report.duplicate_articles_removed == 0
    assert report.newest_catalyst_article is None
    assert report.freshness == CatalystFreshness.UNKNOWN
    assert report.has_breaking_news is False


def test_build_catalyst_report_detects_breaking_catalyst() -> None:
    """Build an active breaking report from a recent recognized catalyst."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    article = create_article(
        "Company announces merger agreement",
        current_time - timedelta(minutes=30),
        sentiment_score=0.40,
    )

    report = build_catalyst_report(
        ticker="XYZ",
        articles=[article],
        original_article_count=1,
        current_time=current_time,
    )

    assert CatalystCategory.MERGER in report.categories
    assert report.historical_categories == []
    assert report.freshness == CatalystFreshness.BREAKING
    assert report.catalyst_strength == CatalystStrength.MODERATE
    assert report.has_breaking_news is True
    assert report.newest_catalyst_article == article.published_at


def test_build_catalyst_report_moves_stale_catalyst_to_history() -> None:
    """Place stale catalyst intelligence into historical context."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    article = create_article("Company reports quarterly earnings", current_time - timedelta(hours=30))

    report = build_catalyst_report(
        ticker="XYZ",
        articles=[article],
        original_article_count=1,
        current_time=current_time,
    )

    assert report.categories == []
    assert CatalystCategory.EARNINGS in report.historical_categories
    assert report.freshness == CatalystFreshness.STALE
    assert report.catalyst_strength == CatalystStrength.WEAK
    assert report.has_breaking_news is False


def test_build_catalyst_report_uses_newest_recognized_catalyst() -> None:
    """Ignore newer unknown articles when determining report freshness."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    catalyst_article = create_article("Company reports quarterly earnings", current_time - timedelta(hours=30))

    unknown_article = create_article("CEO discusses company culture", current_time - timedelta(minutes=30))

    report = build_catalyst_report(
        ticker="XYZ",
        articles=[catalyst_article, unknown_article],
        original_article_count=2,
        current_time=current_time,
    )

    assert report.freshness == CatalystFreshness.STALE
    assert report.newest_catalyst_article == catalyst_article.published_at
    assert report.has_breaking_news is False


def test_build_catalyst_report_calculates_strong_active_catalyst() -> None:
    """Rate multiple fresh catalyst categories as strong."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    article = create_article(
        "Company reports record revenue and receives FDA approval",
        current_time - timedelta(hours=2),
    )

    report = build_catalyst_report(
        ticker="XYZ",
        articles=[article],
        original_article_count=1,
        current_time=current_time,
    )

    assert CatalystCategory.REVENUE_GROWTH in report.categories
    assert CatalystCategory.REGULATORY_APPROVAL in report.categories
    assert report.freshness == CatalystFreshness.FRESH
    assert report.catalyst_strength == CatalystStrength.STRONG


def test_build_catalyst_report_calculates_average_sentiment() -> None:
    """Average article sentiment before classifying overall sentiment."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    articles = [
        create_article(
            "Company reports quarterly earnings",
            current_time - timedelta(hours=2),
            sentiment_score=0.50,
        ),
        create_article(
            "Company announces merger agreement",
            current_time - timedelta(hours=3),
            sentiment_score=0.10,
        ),
    ]

    report = build_catalyst_report(
        ticker="XYZ",
        articles=articles,
        original_article_count=2,
        current_time=current_time,
    )

    assert report.average_sentiment == 0.30
    assert report.overall_sentiment == "Somewhat-Bullish"


def test_build_catalyst_report_tracks_article_counts() -> None:
    """Track original, unique, and removed article counts."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    articles = [
        create_article("Company reports quarterly earnings", current_time),
        create_article("Company announces merger agreement", current_time),
    ]

    report = build_catalyst_report(
        ticker="XYZ",
        articles=articles,
        original_article_count=5,
        current_time=current_time,
    )

    assert report.original_article_count == 5
    assert report.unique_article_count == 2
    assert report.duplicate_articles_removed == 3
