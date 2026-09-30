# STONKS 🚀

```
   _____ _______ ____  _   _ _  __ _____
  / ____|__   __/ __ \| \ | | |/ // ____|
 | (___    | | | |  | |  \| | ' /| (___
  \___ \   | | | |  | | . ` |  <  \___ \
  ____) |  | | | |__| | |\  | . \ ____) |
 |_____/   |_|  \____/|_| \_|_|\_\|____/

    T H E  C I A  I S  W A T C H I N G  Y O U
```

Author: Mario Migliacio, 2026

STONKS is a Python-based stock scanner and trading journal built as both a learning project and a practical trading tool.

The project combines market scanning, public-float analysis, catalyst intelligence, historical data caching, and trade journaling to support data-driven trading decisions.

---

## Current Features

### Scanner

- Live quote retrieval
- Change % and Gap % calculations
- Relative Volume (RVOL)
- Historical volume analysis
- Public-float data enrichment
- Float turnover calculation
- Float size classification
- Scanner candidate model
- Configurable volume filtering

### Float Data

- Public-float data provided by Massive
- Float share and float percentage reporting
- Effective-date tracking
- Local float-data caching
- Configurable cache expiration
- Float turnover (`volume / float_shares`)
- Very Low, Low, Medium, High, and Unknown float classifications
- Graceful fallback when float data is disabled or unavailable

See [Float Data](docs/float_data.md) for details.

### Price Action

- Historical intraday candle retrieval through Massive
- 1-minute, 5-minute, 15-minute, 30-minute, 60-minute, and daily candle timeframes
- Pre-market, regular-session, and after-hours candle selection
- Regular-session price change, high, low, and range analysis
- Configurable recent price-action lookbacks
- Scanner candidate price-action enrichment when intraday data is available
- Cache-first historical intraday data access
- Historical price-action CLI

See [Price Action](docs/price_action.md) for details.

### C.I.A.

**Catalyst Intelligence Analysis**

- Financial news retrieval
- Duplicate article filtering
- Catalyst classification
- Catalyst freshness detection
- Catalyst strength analysis
- Confidence scoring
- Aggregated sentiment analysis
- Active and historical catalyst separation
- Mission brief reporting

See [C.I.A. News Subsystem](docs/cia.md) for details.

### Journal

- Trade order tracking
- Account snapshot tracking
- CSV-based persistence
- Journal backup utility

See [Journal Subsystem](docs/journal.md) for details.

### Caching

- Historical market-data caching
- Intraday candle-data caching
- Public-float caching
- Configurable cache expiration where applicable
- Cache-first API access

See [Historical Cache](docs/cache.md), [Float Data](docs/float_data.md), and [Price Action](docs/price_action.md) for details.

### Development & Quality

- Pytest test suite
- Ruff linting and formatting
- PowerShell development scripts
- GitHub Actions quality checks
- Environment-based API key configuration
- Structured application logging

---

## Project Structure

```text
STONKS/
├── backups/
├── data/
│   ├── cache/
│   │   ├── float/
│   │   ├── historical/
│   │   ├── intraday/
│   │   └── quotes/
│   └── journal/
│       └── templates/
├── docs/
├── scripts/
├── src/
│   └── stonks/
│       ├── api/
│       ├── cache/
│       ├── cia/
│       ├── config/
│       ├── journal/
│       ├── models/
│       ├── news/
│       └── scanner/
├── tests/
│   ├── api/
│   ├── cache/
│   ├── cia/
│   └── scanner/
├── .env
├── pyproject.toml
├── README.md
└── requirements.txt
```

Generated cache, log, backup, virtual-environment, and other runtime files may also exist locally.

---

## Getting Started

Clone the repository:

```powershell
git clone https://github.com/MarioMigliacio/STONKS.git
cd STONKS
```

Initialize the project:

```powershell
.\scripts\init.ps1
```

Activate the virtual environment:

```powershell
.\scripts\activate.ps1
```

Create an Alpha Vantage API key and configure the generated `.env` file:

```text
STONKS_API_KEY=your_api_key
```

Massive provides public-float data and historical aggregate candle data. To use Massive-backed features, create a Massive API key and add:

```text
STONKS_MASSIVE_API_KEY=your_api_key
```

Float-data enrichment can be enabled independently in settings.py:

```python
ENABLE_FLOAT_DATA = True
```

---

## Usage

### Scanner

```powershell
.\scripts\run.ps1
```

### Journal CLI

```powershell
.\scripts\journal.ps1
```

### Historical Cache CLI

```powershell
.\scripts\cache.ps1
```

### Price Action CLI

```powershell
.\scripts\price_action.ps1
```

### News C.I.A. CLI

```powershell
.\scripts\news.ps1
```

### Backup Journal Data

```powershell
.\scripts\backup_journal.ps1
```

### Run Tests

```powershell
.\scripts\test.ps1
```

### Check Formatting and Linting

```powershell
.\scripts\lint.ps1
```

### Apply Formatting Fixes

```powershell
.\scripts\format.ps1
```

### Clean Generated Artifacts

```powershell
.\scripts\clean.ps1

OR cache related files:

.\scripts\clear_cache.ps1
```

---

## Configuration

### Required API Keys

`STONKS_API_KEY`

Alpha Vantage API key used for market and news data.

### Optional API Keys

`STONKS_MASSIVE_API_KEY`

Massive API key used for public-float and aggregate candle data.

Float data is optional. STONKS continues to operate normally when float support is disabled or its provider data is unavailable.

### Optional Features

`ENABLE_FLOAT_DATA`

Controls whether Massive public-float support is enabled.

Defaults to `False`.

---

## Testing & Code Quality

STONKS uses **Pytest** for automated testing and **Ruff** for linting and formatting.

The test suite covers scanner calculations and integration behavior, cache services, API response handling, float-data processing, market-session selection, price-action analysis, and C.I.A. catalyst analysis.

The repository also uses GitHub Actions as a quality gate for automated test and Ruff checks.

Run the local quality checks before submitting changes:

```powershell
.\scripts\lint.ps1
.\scripts\test.ps1
```

---

## Documentation

Detailed subsystem documentation is available under `docs/`:

- [Journal Subsystem](docs/journal.md)
- [Historical Cache](docs/cache.md)
- [C.I.A. News Subsystem](docs/cia.md)
- [Float Data](docs/float_data.md)
- [Price Action](docs/price_action.md)

---

## License

```text
Personal educational project.

Acknowledgement appreciated, but open source.
```
