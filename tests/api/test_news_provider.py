# =============================================================================
# File: test_news_provider.py
# Purpose: Tests the news provider contract and exception hierarchy.
# =============================================================================

import pytest

from stonks.api.exceptions import (
    ProviderAccessError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderRequestError,
)
from stonks.api.providers.news_provider import NewsProvider


def test_news_provider_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        NewsProvider()


def test_news_provider_requires_get_news() -> None:
    class IncompleteProvider(NewsProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.parametrize(
    "exception_type",
    [
        ProviderAuthenticationError,
        ProviderAccessError,
        ProviderRateLimitError,
        ProviderRequestError,
    ],
)
def test_provider_exceptions_share_base_class(
    exception_type: type[ProviderError],
) -> None:
    error = exception_type("Provider failure")

    assert isinstance(error, ProviderError)
    assert str(error) == "Provider failure"
