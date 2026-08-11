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

from stonks.cia.catalyst_category import CatalystCategory
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
            Unique catalyst categories discovered in the news.

        overall_sentiment:
            Human-readable overall sentiment description.

        confidence:
            Confidence in the analysis from 0.0 to 1.0.

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
    """

    ticker: str

    catalyst_strength: CatalystStrength

    categories: list[CatalystCategory]

    overall_sentiment: str

    confidence: float

    summary: str

    article_count: int

    unique_event_count: int

    duplicate_articles_removed: int

    newest_article: datetime