# Historical Data Cache Subsystem

[← Back to Main README](../README.md)

The STONKS Historical Data Cache subsystem exists to reduce API usage, improve development speed, and provide a foundation for advanced scanner features.

---

## Purpose

Many scanner features require access to historical market data.

Examples:

- Relative Volume
- Average Daily Volume
- Moving Averages
- Gap Analysis
- Trend Analysis
- Backtesting

Rather than repeatedly requesting the same data from external APIs, STONKS stores historical market data locally and reuses it whenever possible.

---

## Benefits

### Reduced API Usage

Historical data is downloaded once and reused many times.

Example:

```text
AAPL Daily History

1 API Request
    ↓
100+ Trading Days Returned
    ↓
Unlimited Local Reads
```

This dramatically reduces API consumption and helps stay within free-tier request limits.

---

### Faster Development

During development, STONKS can operate entirely from cached data.

This allows:

- Faster testing
- Offline development
- No accidental API usage
- Consistent test results

---

## Directory Structure

Historical data is stored under:

```text
data/
└── cache/
    ├── quotes/
    └── historical/
```

Example:

```text
data/
└── cache/
    └── historical/
        ├── AAPL_daily.json
        ├── TSLA_daily.json
        └── AMD_daily.json
```

---

## Cache Settings

The cache subsystem is controlled through configuration flags.

```python
USE_CACHE = True

ALLOW_API_CALLS = True
```

### USE_CACHE

When enabled:

```text
True
```

STONKS will attempt to load cached data before making API requests.

---

### ALLOW_API_CALLS

When enabled:

```text
True
```

STONKS may fetch missing data from external APIs.

When disabled:

```text
False
```

STONKS will only use locally cached data.

This is useful when developing features without consuming API requests.

---

## Cache Workflow

```text
Scanner
    ↓
Historical Cache Service
    ↓
Cache Exists?
    ↓
YES ──► Load Local Data
    ↓
 NO
    ↓
API Calls Allowed?
    ↓
YES ──► Fetch From API
    ↓
Save To Cache
    ↓
Return Data

NO ──► Return No Data
```

---

## Creating Historical Cache Data

Launch the cache CLI:

- New update will ask if you want to force a refresh (this is useful if the cache file existed but is out of date)

```powershell
.\scripts\cache.ps1
```

Example:

```text
Symbol to cache: AAPL
Force refresh from API? (Y/N): n
```

First run:

```text
Fetching historical data for AAPL from API...
Historical data ready for AAPL.
```

Subsequent runs:

```text
Using cached historical data for AAPL
Historical data ready for AAPL.
```

Forced Cache refresh option:

```text
Symbol to cache: aapl
Force refresh from API? (Y/N): y
Fetching historical data for AAPL from API...

Parsed 100 historical volume records.
HistoricalVolumeData(trade_date='2026-06-24', volume=53081859)
```

---

## Git Strategy

Cache files are intentionally excluded from Git version control.

Tracked:

```text
data/cache/quotes/.gitkeep
data/cache/historical/.gitkeep
```

Ignored:

```text
*.json
```

This ensures repository size remains small while preserving project structure.

---

## Future Roadmap

Planned features using historical cache data:

- Relative Volume Scanner
- Average Daily Volume
- Moving Averages
- Gap Analysis
- Trend Detection
- Historical Price Statistics
- Backtesting
- Additional Market Data Providers
