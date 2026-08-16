# =============================================================================
# File: cia_engine.py
# Purpose: Builds a normalized C.I.A. CatalystReport from news intelligence.
#
# Notes:
# - Consumes normalized NewsArticle objects.
# - Separates active catalyst intelligence from historical context.
# - Aggregates catalyst categories, sentiment, freshness, and confidence.
# - Does not perform presentation or CLI formatting.
# =============================================================================

from datetime import datetime

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_classifier import classify_article
from stonks.cia.catalyst_freshness import CatalystFreshness
from stonks.cia.catalyst_freshness import calculate_freshness
from stonks.cia.catalyst_freshness import calculate_news_age_minutes
from stonks.cia.catalyst_freshness import find_newest_catalyst_article
from stonks.cia.catalyst_report import CatalystReport
from stonks.cia.catalyst_strength import CatalystStrength
from stonks.models.news_article import NewsArticle


def add_unique_categories(
    destination: list[CatalystCategory],
    categories: list[CatalystCategory]
):
    """Add recognized categories without creating duplicates."""

    for category in categories:

        if category == CatalystCategory.UNKNOWN:
            continue

        if category not in destination:
            destination.append(category)


def collect_catalyst_categories(
    articles: list[NewsArticle],
    current_time: datetime
) -> tuple[list[CatalystCategory], list[CatalystCategory]]:
    """
    Separate active catalyst categories from historical categories.

    BREAKING, FRESH, and RECENT articles are considered active.
    STALE articles are retained as historical context.
    """

    active_categories = []
    historical_categories = []

    for article in articles:
        categories = classify_article(
            article
        )

        if categories == [CatalystCategory.UNKNOWN]:
            continue

        news_age_minutes = calculate_news_age_minutes(
            article.published_at,
            current_time
        )

        freshness = calculate_freshness(
            news_age_minutes
        )

        if freshness in [
            CatalystFreshness.BREAKING,
            CatalystFreshness.FRESH,
            CatalystFreshness.RECENT
        ]:
            add_unique_categories(
                active_categories,
                categories
            )

        else:
            add_unique_categories(
                historical_categories,
                categories
            )

    return (
        active_categories,
        historical_categories
    )


def calculate_average_sentiment(
    articles: list[NewsArticle]
) -> float:
    """Calculate the average sentiment score across all articles."""

    if not articles:
        return 0.0

    sentiment_total = sum(
        article.overall_sentiment_score
        for article in articles
    )

    return sentiment_total / len(articles)


def classify_overall_sentiment(
    average_sentiment: float
) -> str:
    """Classify an average sentiment score."""

    if average_sentiment >= 0.35:
        return "Bullish"

    if average_sentiment >= 0.15:
        return "Somewhat-Bullish"

    if average_sentiment <= -0.35:
        return "Bearish"

    if average_sentiment <= -0.15:
        return "Somewhat-Bearish"

    return "Neutral"


def calculate_catalyst_strength(
    active_categories: list[CatalystCategory],
    freshness: CatalystFreshness
) -> CatalystStrength:
    """
    Calculate catalyst strength using active intelligence only.
    """

    if not active_categories:
        return CatalystStrength.WEAK

    category_count = len(
        active_categories
    )

    if (
        freshness == CatalystFreshness.BREAKING
        and category_count >= 2
    ):
        return CatalystStrength.STRONG

    if freshness == CatalystFreshness.BREAKING:
        return CatalystStrength.MODERATE

    if (
        freshness == CatalystFreshness.FRESH
        and category_count >= 2
    ):
        return CatalystStrength.STRONG

    if freshness == CatalystFreshness.FRESH:
        return CatalystStrength.MODERATE

    if freshness == CatalystFreshness.RECENT:
        return CatalystStrength.MODERATE

    return CatalystStrength.WEAK


def calculate_confidence(
    articles: list[NewsArticle]
) -> float:
    """
    Calculate confidence from the percentage of articles that contain
    recognized catalyst intelligence.
    """

    if not articles:
        return 0.0

    recognized_article_count = 0

    for article in articles:
        categories = classify_article(
            article
        )

        if categories != [CatalystCategory.UNKNOWN]:
            recognized_article_count += 1

    confidence = (
        recognized_article_count / len(articles)
    )

    return round(
        confidence,
        2
    )


def build_summary(
    ticker: str,
    active_categories: list[CatalystCategory],
    historical_categories: list[CatalystCategory],
    freshness: CatalystFreshness
) -> str:
    """Build a deterministic day-trading focused C.I.A. summary."""

    if active_categories:
        active_text = ", ".join(
            category.value
            for category in active_categories
        )

        return (
            f"{ticker} has active catalyst intelligence involving "
            f"{active_text}. "
            f"The newest recognized catalyst is "
            f"{freshness.value.lower()}."
        )

    if historical_categories:
        return (
            f"No active catalyst intelligence was identified for {ticker}. "
            f"Older catalyst activity exists, but the newest recognized "
            f"intelligence is {freshness.value.lower()}."
        )

    return (
        f"No significant catalyst intelligence "
        f"was identified for {ticker}."
    )


def build_catalyst_report(
    ticker: str,
    articles: list[NewsArticle],
    original_article_count: int,
    current_time: datetime
) -> CatalystReport:
    """Build a complete C.I.A. CatalystReport."""

    (
        active_categories,
        historical_categories
    ) = collect_catalyst_categories(
        articles,
        current_time
    )

    newest_catalyst = find_newest_catalyst_article(
        articles
    )

    if newest_catalyst:
        news_age_minutes = calculate_news_age_minutes(
            newest_catalyst.published_at,
            current_time
        )

        freshness = calculate_freshness(
            news_age_minutes
        )

        newest_article_time = (
            newest_catalyst.published_at
        )
    else:
        news_age_minutes = 0
        freshness = CatalystFreshness.UNKNOWN
        newest_article_time = current_time

    catalyst_strength = calculate_catalyst_strength(
        active_categories,
        freshness
    )

    average_sentiment = calculate_average_sentiment(
        articles
    )

    overall_sentiment = classify_overall_sentiment(
        average_sentiment
    )

    confidence = calculate_confidence(
        articles
    )

    summary = build_summary(
        ticker,
        active_categories,
        historical_categories,
        freshness
    )

    duplicate_articles_removed = (
        original_article_count - len(articles)
    )

    return CatalystReport(
        ticker=ticker,
        catalyst_strength=catalyst_strength,
        categories=active_categories,
        historical_categories=historical_categories,
        overall_sentiment=overall_sentiment,
        average_sentiment=average_sentiment,
        confidence=confidence,
        summary=summary,
        article_count=original_article_count,

        # NOTE:
        # This currently represents unique filtered articles.
        # True event-level deduplication is future C.I.A. work.
        unique_event_count=len(articles),

        duplicate_articles_removed=duplicate_articles_removed,
        newest_article=newest_article_time,
        freshness=freshness,
        news_age_minutes=news_age_minutes,
        has_breaking_news=(
            freshness == CatalystFreshness.BREAKING
        )
    )