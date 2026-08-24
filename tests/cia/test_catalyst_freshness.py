# =============================================================================
# File: test_catalyst_freshness.py
# Purpose: Pytest file for catalyst_freshness.py.
# =============================================================================

from datetime import datetime, timedelta, timezone

import pytest

from stonks.cia.catalyst_freshness import (
    CatalystFreshness,
    calculate_freshness,
    calculate_news_age_minutes,
    find_newest_catalyst_article,
)
from stonks.models.news_article import NewsArticle


def create_article(title: str, published_at: datetime) -> NewsArticle:
    """Create a minimal NewsArticle for freshness tests."""

    return NewsArticle(
        title=title,
        source="Test Source",
        published_at=published_at,
        summary="Test article summary.",
        url="https://example.com/article",
        sentiment_score=0.0,
        sentiment_label="Neutral",
    )


@pytest.mark.parametrize(
    "age_minutes, expected_freshness",
    [
        (60, CatalystFreshness.BREAKING),
        (61, CatalystFreshness.FRESH),
        (240, CatalystFreshness.FRESH),
        (241, CatalystFreshness.RECENT),
        (1440, CatalystFreshness.RECENT),
        (1441, CatalystFreshness.STALE),
    ],
)
def test_calculate_freshness_boundaries(age_minutes: int, expected_freshness: CatalystFreshness) -> None:
    """Classify freshness correctly at configured boundaries."""

    freshness = calculate_freshness(age_minutes)

    assert freshness == expected_freshness


def test_calculate_news_age_minutes() -> None:
    """Calculate article age in whole minutes."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    published_at = current_time - timedelta(minutes=125)

    news_age_minutes = calculate_news_age_minutes(published_at, current_time)

    assert news_age_minutes == 125


def test_calculate_news_age_minutes_clamps_future_time_to_zero() -> None:
    """Treat slightly future-dated provider timestamps as zero minutes old."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    published_at = current_time + timedelta(minutes=5)

    news_age_minutes = calculate_news_age_minutes(published_at, current_time)

    assert news_age_minutes == 0


def test_find_newest_catalyst_article() -> None:
    """Return the newest article containing a recognized catalyst."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    older_article = create_article("Company reports quarterly earnings", current_time - timedelta(hours=8))

    newer_article = create_article("Company announces merger agreement", current_time - timedelta(hours=2))

    newest_catalyst = find_newest_catalyst_article([older_article, newer_article])

    assert newest_catalyst == newer_article


def test_find_newest_catalyst_article_ignores_unknown_articles() -> None:
    """Ignore newer articles that contain no recognized catalyst."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    catalyst_article = create_article("Company reports quarterly earnings", current_time - timedelta(hours=8))

    unknown_article = create_article("CEO discusses company culture", current_time - timedelta(minutes=30))

    newest_catalyst = find_newest_catalyst_article([catalyst_article, unknown_article])

    assert newest_catalyst == catalyst_article


def test_find_newest_catalyst_article_returns_none_when_none_recognized() -> None:
    """Return None when no article contains catalyst intelligence."""

    current_time = datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)

    article = create_article("CEO discusses company culture", current_time)

    newest_catalyst = find_newest_catalyst_article([article])

    assert newest_catalyst is None
