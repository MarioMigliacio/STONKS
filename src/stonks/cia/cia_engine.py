# =============================================================================
# File: cia_engine.py
# Purpose: Builds a normalized C.I.A. CatalystReport from news intelligence.
#
# Notes:
# - Consumes normalized NewsArticle objects.
# - Aggregates catalyst categories, sentiment, freshness, and confidence.
# - Does not perform presentation or CLI formatting.
# - AI summarization and advanced weighting belong to future C.I.A. versions.
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


def collect_catalyst_categories(
    articles: list[NewsArticle]
) -> list[CatalystCategory]:
    """Collect unique recognized catalyst categories from news articles."""

    categories = []

    for article in articles:
        article_categories = classify_article(
            article
        )

        for category in article_categories:

            if category == CatalystCategory.UNKNOWN:
                continue

            if category not in categories:
                categories.append(category)

    return categories


def calculate_overall_sentiment(
    articles: list[NewsArticle]
) -> str:
    """Calculate a simple overall sentiment label from article scores."""

    if not articles:
        return "Unknown"

    sentiment_total = sum(
        article.overall_sentiment_score
        for article in articles
    )

    average_sentiment = (
        sentiment_total / len(articles)
    )

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
    categories: list[CatalystCategory],
    freshness: CatalystFreshness
) -> CatalystStrength:
    """
    Calculate a simple catalyst strength from category count and freshness.

    This intentionally remains conservative for C.I.A. v1.
    """

    if not categories:
        return CatalystStrength.UNKNOWN

    category_count = len(categories)

    if (
        freshness == CatalystFreshness.BREAKING
        and category_count >= 2
    ):
        return CatalystStrength.STRONG

    if (
        freshness in [
            CatalystFreshness.BREAKING,
            CatalystFreshness.FRESH
        ]
    ):
        return CatalystStrength.MODERATE

    if category_count >= 2:
        return CatalystStrength.MODERATE

    return CatalystStrength.WEAK


def calculate_confidence(
    articles: list[NewsArticle],
    categories: list[CatalystCategory]
) -> float:
    """
    Calculate a basic confidence score for the C.I.A. report.

    Confidence is intentionally simple in v1.
    """

    if not articles or not categories:
        return 0.0

    recognized_article_count = 0

    for article in articles:
        article_categories = classify_article(
            article
        )

        if article_categories != [CatalystCategory.UNKNOWN]:
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
    categories: list[CatalystCategory],
    freshness: CatalystFreshness
) -> str:
    """Build a simple deterministic C.I.A. summary."""

    if not categories:
        return (
            f"No significant catalyst intelligence "
            f"was identified for {ticker}."
        )

    category_text = ", ".join(
        category.value
        for category in categories
    )

    return (
        f"{ticker} has recognized catalyst activity involving "
        f"{category_text}. "
        f"The newest recognized catalyst is {freshness.value.lower()}."
    )


def build_catalyst_report(
    ticker: str,
    articles: list[NewsArticle],
    original_article_count: int,
    current_time: datetime
) -> CatalystReport:
    """Build a complete C.I.A. CatalystReport."""

    categories = collect_catalyst_categories(
        articles
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
        categories,
        freshness
    )

    overall_sentiment = calculate_overall_sentiment(
        articles
    )

    confidence = calculate_confidence(
        articles,
        categories
    )

    summary = build_summary(
        ticker,
        categories,
        freshness
    )

    duplicate_articles_removed = (
        original_article_count - len(articles)
    )

    return CatalystReport(
        ticker=ticker,
        catalyst_strength=catalyst_strength,
        categories=categories,
        overall_sentiment=overall_sentiment,
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