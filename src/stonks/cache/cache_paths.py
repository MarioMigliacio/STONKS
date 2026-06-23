# =============================================================================
# File: cache_paths.py
# Purpose: Defines local cache paths used by STONKS.
# =============================================================================

from pathlib import Path

CACHE_DIRECTORY = Path("data/cache")
QUOTE_CACHE_DIRECTORY = CACHE_DIRECTORY / "quotes"
HISTORICAL_CACHE_DIRECTORY = CACHE_DIRECTORY / "historical"

def ensure_cache_directories_exist():
    """Create cache directories if they do not already exist."""

    QUOTE_CACHE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    HISTORICAL_CACHE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )