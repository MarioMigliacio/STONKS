# =============================================================================
# File: news_provider.py
# Purpose: Defines the common interface for financial news providers.
# =============================================================================

from abc import ABC, abstractmethod

from stonks.models.news_article import NewsArticle


class NewsProvider(ABC):
    """Defines the interface for retrieving normalized financial news."""

    @abstractmethod
    def get_news(
        self,
        symbol: str,
        limit: int = 50,
    ) -> list[NewsArticle]:
        """Retrieve news articles for a ticker symbol."""
        raise NotImplementedError
