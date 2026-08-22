# =============================================================================
# File: news_article.py
# Purpose: Defines normalized news article data used by STONKS.
#
# Notes:
# - Provides a provider-independent article model for scanner and C.I.A. logic.
# - Additional providers can normalize their responses into this same model.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsArticle:
    """
    Represents one normalized market news article.

    Attributes:
        title:
            Article headline.

        source:
            Publisher or news source.

        published_at:
            Provider timestamp for the article.

        summary:
            Short article summary.

        url:
            Link to the original article.

        sentiment_score:
            Sentiment score for the stock ticker being analyzed.

        sentiment_label:
            Human-readable sentiment label for the stock ticker being analyzed.
    """

    title: str
    source: str
    published_at: datetime
    summary: str
    url: str
    sentiment_score: float
    sentiment_label: str