# =============================================================================
# File: catalyst_report.py
# Purpose: Defines the normalized intelligence report produced by C.I.A.
#
# Notes:
# - CatalystReport is the primary output model for Catalyst Intelligence
#   Analysis.
# - Future classification, duplicate detection, scoring, and AI summarization
#   systems will populate this model.
# - Scanner code should eventually consume CatalystReport rather than raw
#   NewsArticle collections.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_freshness import CatalystFreshness
from stonks.cia.catalyst_strength import CatalystStrength


@dataclass
class CatalystReport:
    """
    Represents a C.I.A. intelligence report for one stock ticker.

    Attributes:
        ticker:
            Stock ticker being analyzed.

        catalyst_strength:
            Overall assessed strength of the discovered catalysts.

        categories:
            Unique catalyst categories discovered in the news that are within the freshness constants in the config settings.

        historical_categories:
            Unique catalyst categories that fall outside the freshness constants in the config settings.

        average_sentiment:
            News sentiment aggregated into average value across collection of news objects.

        overall_sentiment:
            Human-readable overall sentiment description.

        confidence:
            The proportion of analyzed articles that contained recognized catalyst intelligence from 0.0 to 1.0.

        summary:
            Human-readable catalyst summary.

        article_count:
            Total number of articles considered.

        unique_event_count:
            Number of distinct events after duplicate removal.

        duplicate_articles_removed:
            Number of duplicate or redundant articles removed.

        newest_article:
            Publication time of the newest article considered.

        freshness:
            Freshness classification of the newest recognized catalyst.

        news_age_minutes:
            Age in minutes of the newest recognized catalyst.

        has_breaking_news:
            True when a recognized catalyst falls within the configured
            breaking-news window.
    """

    ticker: str

    catalyst_strength: CatalystStrength

    categories: list[CatalystCategory]

    historical_categories: list[CatalystCategory]

    average_sentiment: float

    overall_sentiment: str

    confidence: float

    summary: str

    original_article_count: int

    unique_article_count: int

    duplicate_articles_removed: int

    newest_catalyst_article: Optional[datetime]

    freshness: CatalystFreshness

    news_age_minutes: int

    has_breaking_news: bool