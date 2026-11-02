# Historical Research

[← Back to Main README](../README.md)

## Overview

Historical Research provides a unified interface for retrieving and analyzing historical stock-price candles.

It supports intraday and calendar-based research using existing STONKS market-data providers and caches.

The public entry point is:

`stonks.price_action.research_runner.run_historical_research()`

The research pipeline is independent of the desktop GUI.

## Supported Intervals

| Chart interval                    | Source candles | Provider      |
| --------------------------------- | -------------- | ------------- |
| 1, 5, 10, 15, 30, 60 minutes      | 1-minute       | Massive       |
| Daily, weekly, monthly, quarterly | Daily          | Alpha Vantage |

Chart intervals are generated locally from source candles. Changing the display interval does not inherently require a different provider request.

Intraday requests currently support a single trading date. Calendar-based requests support a date range.

## Research Request

`HistoricalResearchRequest` contains:

- Stock ticker
- Inclusive start and end dates
- Display interval
- Optional intraday market session
- Optional analysis-window boundaries
- Optional force-refresh flag

Ticker symbols are normalized to uppercase.

Analysis-window boundaries must be timezone-aware and use an inclusive start and exclusive end.

## Retrieval and Caching

The research runner delegates retrieval to the existing cache services:

- `retrieve_intraday_data()` for Massive one-minute candles.
- `retrieve_daily_research_data()` for Alpha Vantage daily candles.

Both return `ResearchDataRetrieval`, which records source candles, provenance, retrieval status, and an optional explanation.

Successful cache hits avoid provider requests. Explicit refresh bypasses the cache.

Provider failures during refresh are reported rather than silently replaced with older cached candles.

## Retrieval Statuses

| Status           | Meaning                                                           |
| ---------------- | ----------------------------------------------------------------- |
| `SUCCESS`        | One or more normalized source candles were retrieved              |
| `NO_DATA`        | The provider returned no candles for the requested period         |
| `API_DISABLED`   | API access is disabled and usable cached data is unavailable      |
| `PROVIDER_ERROR` | The provider request or response failed                           |
| `CACHE_ERROR`    | Cached data is invalid or unreadable and retrieval cannot recover |

The research runner converts these into `HistoricalResearchResult` statuses: `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, or `ERROR`.

## Aggregation and Analysis

Intraday display candles are aggregated from one-minute source candles.

Calendar display candles are aggregated from daily source candles.

OHLCV aggregation uses the first open, highest high, lowest low, last close, and summed volume.

Analysis-window metrics are calculated directly from source candles, independently of the selected chart interval.

Metrics include:

- Percentage price change
- Highest and lowest prices
- Percentage price range
- Total volume
- Source candle count

## Known Limitations

- A successful retrieval does not guarantee complete coverage of the requested date range.
- Partial-data detection currently identifies missing one-minute candles within populated display buckets; it does not identify every absent bucket.
- Daily, weekly, monthly, and quarterly aggregation does not validate exchange-calendar completeness.
- Market sessions use fixed Eastern Time boundaries and do not yet account for all exchange holidays or early closes.
- Historical coverage depends on the configured provider subscription and API availability.
- Daily candles use UTC midnight to represent the trading date, rather than the actual exchange session opening time.
- The current research runner executes synchronously. Background execution and cancellation are planned for subsequent milestone work.

Provider access is subject to the configured API permissions and cache availability.
