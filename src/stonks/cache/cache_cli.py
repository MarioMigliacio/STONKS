# =============================================================================
# File: cache_cli.py
# Purpose: Provides command-line tools for cache testing.
# =============================================================================

from stonks.cache.historical_cache_service import get_historical_data

def main():
    """Run the cache CLI."""

    symbol = input("Symbol to cache: ").strip().upper()

    if not symbol:
        print("Symbol cannot be empty.")
        return

    data = get_historical_data(symbol)

    if not data:
        print("No data returned.")
        return

    print("")
    print(f"Historical data ready for {symbol}.")

if __name__ == "__main__":
    main()