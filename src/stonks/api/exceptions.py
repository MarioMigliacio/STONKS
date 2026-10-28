# =============================================================================
# File: exceptions.py
# Purpose: Defines errors raised by external market data providers.
# =============================================================================


class ProviderError(Exception):
    """Base exception for external data provider failures."""


class ProviderAuthenticationError(ProviderError):
    """Raised when provider credentials are invalid or missing."""


class ProviderAccessError(ProviderError):
    """Raised when a provider endpoint requires additional access."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider's request limit has been reached."""


class ProviderRequestError(ProviderError):
    """Raised when a provider request or response fails."""
