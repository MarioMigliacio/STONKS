# =============================================================================
# File: marketaux.py
# Purpose: Retrieves and normalizes financial news from Marketaux.
# =============================================================================

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from stonks.api.exceptions import (
    ProviderAccessError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from stonks.api.providers.news_provider import NewsProvider
from stonks.config import settings
from stonks.models.news_article import NewsArticle

logger = logging.getLogger(__name__)

MARKETAUX_NEWS_URL = "https://api.marketaux.com/v1/news/all"

# Conservative initial limit for Marketaux's free plan.
MARKETAUX_MAX_ARTICLES = 3


class MarketauxNewsProvider(NewsProvider):
    """Retrieves ticker-specific news using the Marketaux API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.m_api_key = api_key if api_key is not None else settings.MARKETAUX_API_KEY

    def get_news(
        self,
        symbol: str,
        limit: int = 50,
    ) -> list[NewsArticle]:
        """Fetch and normalize articles for a ticker symbol."""

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("Ticker symbol cannot be empty.")

        if limit < 1:
            raise ValueError("Article limit must be positive.")

        if not self.m_api_key:
            raise ProviderAuthenticationError("Missing STONKS_MARKETAUX_API_KEY.")

        requested_limit = min(limit, MARKETAUX_MAX_ARTICLES)

        params = {
            "api_token": self.m_api_key,
            "symbols": symbol,
            "filter_entities": "true",
            "language": "en",
            "limit": requested_limit,
        }

        logger.debug(
            "Requesting up to %d Marketaux articles for %s",
            requested_limit,
            symbol,
        )

        try:
            response = requests.get(
                MARKETAUX_NEWS_URL,
                params=params,
                timeout=15,
            )
        except requests.RequestException as error:
            raise ProviderRequestError(f"Marketaux request failed for {symbol}.") from error

        self._validate_response(response)

        try:
            payload = response.json()
        except ValueError as error:
            raise ProviderRequestError("Marketaux returned invalid JSON.") from error

        if not isinstance(payload, dict):
            raise ProviderRequestError("Marketaux returned an unexpected response.")

        if "error" in payload:
            self._raise_api_error(payload["error"])

        data = payload.get("data")

        if not isinstance(data, list):
            raise ProviderRequestError("Marketaux response is missing its article list.")

        articles = [self._parse_article(item, symbol) for item in data]

        logger.debug(
            "Marketaux returned %d articles for %s",
            len(articles),
            symbol,
        )

        return articles

    @staticmethod
    def _validate_response(response: requests.Response) -> None:
        """Translate HTTP failures into provider exceptions."""

        status = response.status_code

        if status == 401:
            raise ProviderAuthenticationError("Marketaux rejected the API credentials.")

        if status == 402:
            raise ProviderRateLimitError("Marketaux plan usage limit has been reached.")

        if status == 403:
            raise ProviderAccessError("Marketaux endpoint is restricted by the current plan.")

        if status == 429:
            raise ProviderRateLimitError("Marketaux request rate limit has been reached.")

        if status != 200:
            raise ProviderRequestError(f"Marketaux returned HTTP {status}.")

    @staticmethod
    def _raise_api_error(error: Any) -> None:
        """Translate API error codes returned in JSON."""

        if not isinstance(error, dict):
            raise ProviderRequestError("Marketaux returned an API error.")

        code = error.get("code", "unknown")

        if code == "invalid_api_token":
            raise ProviderAuthenticationError("Marketaux rejected the API credentials.")

        if code == "endpoint_access_restricted":
            raise ProviderAccessError("Marketaux endpoint requires additional access.")

        if code in ("usage_limit_reached", "rate_limit_reached"):
            raise ProviderRateLimitError(f"Marketaux limit reached: {code}.")

        raise ProviderRequestError(f"Marketaux API error: {code}.")

    @staticmethod
    def _parse_article(
        item: Any,
        symbol: str,
    ) -> NewsArticle:
        """Convert a Marketaux article into the STONKS model."""

        if not isinstance(item, dict):
            raise ProviderRequestError("Marketaux returned a malformed article.")

        try:
            published_text = item["published_at"]
            published_at = datetime.fromisoformat(published_text.replace("Z", "+00:00"))

            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)

            entities = item["entities"]

            if not isinstance(entities, list):
                raise ValueError("Invalid entity list.")

            matching_entity = next(
                entity
                for entity in entities
                if isinstance(entity, dict) and str(entity.get("symbol", "")).upper() == symbol
            )

            raw_sentiment = matching_entity.get("sentiment_score")

            if raw_sentiment is None:
                sentiment_score = 0.0
                sentiment_label = "Unknown"
            else:
                sentiment_score = float(raw_sentiment)

                if not -1.0 <= sentiment_score <= 1.0:
                    raise ValueError("Invalid sentiment score.")

                if sentiment_score > 0:
                    sentiment_label = "Bullish"
                elif sentiment_score < 0:
                    sentiment_label = "Bearish"
                else:
                    sentiment_label = "Neutral"

            return NewsArticle(
                title=str(item["title"]),
                source=str(item["source"]),
                published_at=published_at,
                summary=str(item.get("description") or item.get("snippet") or ""),
                url=str(item["url"]),
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
            )

        except (KeyError, TypeError, ValueError, StopIteration) as error:
            raise ProviderRequestError("Marketaux returned an invalid article.") from error
