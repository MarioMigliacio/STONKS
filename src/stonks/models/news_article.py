# =============================================================================
# File: news_article.py
# Purpose: Defines normalized news article data used by STONKS.
#
# Notes:
# - Isolates scanner logic from provider-specific JSON fields.
# - Additional providers can normalize their responses into this same model.
# =============================================================================

from dataclasses import dataclass

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

        overall_sentiment_score:
            Provider-generated sentiment score.

        overall_sentiment_label:
            Provider-generated sentiment label.
    """

    title: str
    source: str
    published_at: str
    summary: str
    url: str
    overall_sentiment_score: float
    overall_sentiment_label: str