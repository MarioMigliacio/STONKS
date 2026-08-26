# =============================================================================
# File: cache_cli.py
# Purpose: Provides command-line tools for cache testing.
# =============================================================================

from stonks.cache.historical_cache_service import get_historical_data
from stonks.scanner.historical_volume_parser import parse_historical_volumes


def main():
    """Run the cache CLI."""

    symbol = input("Symbol to cache: ").strip().upper()

    if not symbol:
        print("Symbol cannot be empty.")
        return

    refresh_choice = input("Force refresh from API? (Y/N): ").strip().lower()
    force_refresh = refresh_choice == "y"

    data = get_historical_data(symbol, force_refresh=force_refresh)

    if not data:
        print("No data returned.")
        return

    volumes = parse_historical_volumes(data)

    print("")
    print(f"Parsed {len(volumes)} historical volume records.")

    if volumes:
        print(volumes[0])

    print("")
    print(f"Historical data ready for {symbol}.")


if __name__ == "__main__":
    main()
