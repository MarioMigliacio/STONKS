# =============================================================================
# File: catalyst_freshness.py
# Purpose: Determines the freshness of C.I.A. catalyst intelligence.
#
# Notes:
# - Freshness is intentionally separate from catalyst strength and sentiment.
# - Day trading places greater importance on newly published catalysts.
# - Only meaningful catalyst articles should be considered when determining
#   the freshness of a CatalystReport.
# =============================================================================

from datetime import datetime
from enum import Enum
from typing import Optional

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_classifier import classify_article
from stonks.models.news_article import NewsArticle
from stonks.config.settings import CIA_BREAKING_NEWS_MINUTES
from stonks.config.settings import CIA_FRESH_NEWS_HOURS
from stonks.config.settings import CIA_RECENT_NEWS_HOURS


class CatalystFreshness(Enum):
    """Represents how recently catalyst intelligence was published."""

    UNKNOWN = "Unknown"
    BREAKING = "Breaking"
    FRESH = "Fresh"
    RECENT = "Recent"
    STALE = "Stale"

def find_newest_catalyst_article(
    articles: list[NewsArticle]
) -> Optional[NewsArticle]:
    """Find the newest article containing a recognized catalyst."""

    catalyst_articles = []

    for article in articles:
        categories = classify_article(
            article
        )

        if categories != [CatalystCategory.UNKNOWN]:
            catalyst_articles.append(article)

    if not catalyst_articles:
        return None

    return max(
        catalyst_articles,
        key=lambda article: article.published_at
    )


def calculate_news_age_minutes(
    published_at: datetime,
    current_time: datetime
) -> int:
    """Calculate the age of an article in minutes."""

    difference = current_time - published_at

    return max(
        0,
        int(difference.total_seconds() / 60)
    )


def calculate_freshness(
    news_age_minutes: int
) -> "CatalystFreshness":
    """Determine catalyst freshness from its age."""

    if news_age_minutes <= CIA_BREAKING_NEWS_MINUTES:
        return CatalystFreshness.BREAKING

    if news_age_minutes <= CIA_FRESH_NEWS_HOURS * 60:
        return CatalystFreshness.FRESH

    if news_age_minutes <= CIA_RECENT_NEWS_HOURS * 60:
        return CatalystFreshness.RECENT

    return CatalystFreshness.STALE