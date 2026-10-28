# =============================================================================
# File: test_marketaux.py
# Purpose: Tests Marketaux news retrieval and response normalization.
# =============================================================================

from datetime import timezone
from unittest.mock import Mock, patch

import pytest
import requests

from stonks.api.exceptions import (
    ProviderAccessError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from stonks.api.providers.marketaux import MarketauxNewsProvider


@pytest.fixture
def provider() -> MarketauxNewsProvider:
    return MarketauxNewsProvider(api_key="test-key")


def make_response(status: int, payload: dict) -> Mock:
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    return response


def test_normalizes_ticker_specific_article(provider) -> None:
    payload = {
        "data": [
            {
                "title": "AMD announces new contract",
                "source": "example.com",
                "published_at": "2026-10-28T12:30:00Z",
                "description": "A major new contract.",
                "url": "https://example.com/amd",
                "entities": [
                    {"symbol": "NVDA", "sentiment_score": -0.8},
                    {"symbol": "AMD", "sentiment_score": 0.65},
                ],
            }
        ]
    }

    with patch(
        "stonks.api.providers.marketaux.requests.get",
        return_value=make_response(200, payload),
    ) as request:
        articles = provider.get_news("amd")

    assert len(articles) == 1
    assert articles[0].title == "AMD announces new contract"
    assert articles[0].sentiment_score == 0.65
    assert articles[0].sentiment_label == "Bullish"
    assert articles[0].published_at.tzinfo == timezone.utc

    params = request.call_args.kwargs["params"]
    assert params["symbols"] == "AMD"
    assert params["limit"] == 3


def test_empty_feed_returns_empty_list(provider) -> None:
    with patch(
        "stonks.api.providers.marketaux.requests.get",
        return_value=make_response(200, {"data": []}),
    ):
        assert provider.get_news("MSFT") == []


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, ProviderAuthenticationError),
        (402, ProviderRateLimitError),
        (403, ProviderAccessError),
        (429, ProviderRateLimitError),
        (500, ProviderRequestError),
    ],
)
def test_http_errors(provider, status, expected) -> None:
    with patch(
        "stonks.api.providers.marketaux.requests.get",
        return_value=make_response(status, {}),
    ):
        with pytest.raises(expected):
            provider.get_news("AMD")


def test_network_error(provider) -> None:
    with patch(
        "stonks.api.providers.marketaux.requests.get",
        side_effect=requests.Timeout(),
    ):
        with pytest.raises(ProviderRequestError):
            provider.get_news("AMD")


def test_invalid_payload(provider) -> None:
    with patch(
        "stonks.api.providers.marketaux.requests.get",
        return_value=make_response(200, {"unexpected": []}),
    ):
        with pytest.raises(ProviderRequestError):
            provider.get_news("AMD")


def test_missing_api_key() -> None:
    provider = MarketauxNewsProvider(api_key="")

    with pytest.raises(ProviderAuthenticationError):
        provider.get_news("AMD")
