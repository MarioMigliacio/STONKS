# =============================================================================
# File: price_action_cli.py
# Purpose: Provides a CLI for inspecting historical intraday stock price action.
# =============================================================================

import logging
from datetime import date
from typing import Optional

from stonks.cache.intraday_cache_service import get_intraday_data
from stonks.config.settings import PRICE_ACTION_LOOKBACKS
from stonks.log_manager import configure_logging
from stonks.models.market_session import MarketSession
from stonks.models.price_action_data import PriceActionData
from stonks.models.price_action_summary import PriceActionSummary
from stonks.models.timeframe import Timeframe
from stonks.scanner.price_action import build_price_action_summary

logger = logging.getLogger(__name__)


def run_price_action_cli():
    """Run the interactive price-action CLI."""

    configure_logging()

    print()
    print("=" * 60)
    print("STONKS PRICE ACTION")
    print("=" * 60)

    symbol = input("Ticker: ").strip().upper()
    trading_date = _prompt_for_date()

    candles = get_intraday_data(
        symbol=symbol,
        timeframe=Timeframe.ONE_MINUTE,
        start_date=trading_date,
        end_date=trading_date,
    )

    if not candles:
        print()
        print(f"No intraday data available for {symbol} on {trading_date}.")
        return

    summary = build_price_action_summary(
        candles=candles,
        session=MarketSession.REGULAR,
        lookbacks=PRICE_ACTION_LOOKBACKS,
    )

    _print_price_action_summary(
        symbol=symbol,
        trading_date=trading_date,
        raw_candle_count=len(candles),
        summary=summary,
    )


def _prompt_for_date() -> date:
    """Prompt until the user enters a valid ISO-formatted date."""

    while True:
        value = input("Date (YYYY-MM-DD): ").strip()

        try:
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Please use YYYY-MM-DD.")


def _print_price_action_summary(
    symbol: str,
    trading_date: date,
    raw_candle_count: int,
    summary: PriceActionSummary,
):
    """Print a formatted price-action summary."""

    print()
    print(f"Ticker:      {symbol}")
    print(f"Date:        {trading_date}")
    print(f"Session:     {summary.session.value}")
    print(f"Raw Candles: {raw_candle_count}")

    print()
    print("SESSION PRICE ACTION")
    print("-" * 60)
    _print_price_action_data(summary.session_data)

    print()
    print("RECENT PRICE ACTION")
    print("-" * 60)

    for lookback, price_action in summary.lookbacks.items():
        print(f"{lookback} minute(s)")
        _print_price_action_data(
            price_action,
            indent="  ",
        )
        print()


def _print_price_action_data(
    price_action: PriceActionData,
    indent: str = "",
):
    """Print calculated price-action metrics."""

    print(f"{indent}Change: {_format_percent(price_action.change_percent)}")
    print(f"{indent}High:   {_format_price(price_action.high_price)}")
    print(f"{indent}Low:    {_format_price(price_action.low_price)}")
    print(f"{indent}Range:  {_format_percent(price_action.range_percent)}")


def _format_percent(
    value: Optional[float],
) -> str:
    """Format a percentage value for CLI output."""

    if value is None:
        return "Unavailable"

    return f"{value:+.2f}%"


def _format_price(
    value: Optional[float],
) -> str:
    """Format a stock price for CLI output."""

    if value is None:
        return "Unavailable"

    return f"${value:.2f}"


if __name__ == "__main__":
    run_price_action_cli()
