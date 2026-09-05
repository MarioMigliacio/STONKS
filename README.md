# STONKS 🚀

Author: Mario Migliacio, 2026

STONKS is a Python-based stock scanner and trading journal built as both a learning project and a practical trading tool.

The project focuses on:

- Market data collection
- Stock scanner development
- Trade journaling
- Performance analytics
- Historical data caching
- Trading discipline through data-driven decision making

---

## Current Features

### Scanner

- Live quote retrieval
- Change % scanner
- Gap % scanner
- Relative Volume scanner
- Historical data cache subsystem
- Ticker-specific financial news retrieval
- Provider-generated news sentiment
- C.I.A. catalyst intelligence foundation

### Journal

- Trade order tracking
- Account snapshot tracking
- CSV-based persistence
- Journal backup utility

### C.I.A.

- Financial news retrieval
- Duplicate article filtering
- Catalyst classification
- Breaking-news freshness detection
- Catalyst strength and confidence
- Aggregated sentiment analysis
- Mission brief reporting

---

## Project Structure

```text
STONKS/
├── backups/
├── data/
|   ├── cache/
|   |   ├── historical/
|   |   └── quotes/
│   └── journal/
│       └── templates/
├── docs/
├── scripts/
├── src/
│   └── stonks/
│       ├── api/
|       ├── cache/
|       ├── cia/
|       ├── config/
│       ├── journal/
|       ├── models/
|       ├── news/
|       └── scanner/
├── tests/
│   ├── cia/
│   └── scanner/
├── venv/
├── .env (secret)
├── pyproject.toml (for pytest path consistency)
├── README.md
└── requirements.txt (dependencies)

```

---

## How To Get started

```
- on a terminal, create and cd into a directory to house the repo.
- run git clone https://github.com/MarioMigliacio/STONKS.git
- cd into STONKS/
- run ".\scripts\init.ps1"
- run ".\scripts\activate.ps1"
- visit https://www.alphavantage.co/support/# 'Claim your API key' and update .env file as described in init.ps1
- Optionally, visit https://www.massive.com and create an API key.
- Add STONKS_MASSIVE_API_KEY to your .env file.
- Set ENABLE_FLOAT_DATA = True in settings.py.
- . . .
- profit
```

---

## Usage

### Run Scanner

```powershell
.\scripts\run.ps1
```

### Clean Artifacts

```powershell
.\scripts\clean.ps1
```

### Journal CLI

```powershell
.\scripts\journal.ps1
```

### Historical Cache CLI

```powershell
.\scripts\cache.ps1
```

### Backup Journal Data

```powershell
.\scripts\backup_journal.ps1
```

### News C.I.A CLI

```powershell
.\scripts\news.ps1
```

### Test Framework

```powershell
.\scripts\test.ps1
```

### Lint format checking (non mutative)

```powershell
.\scripts\lint.ps1
```

### Fix Linting Format (mutative)

```powershell
.\scripts\format.ps1
```

---

## Configuration

```
Required API Keys

STONKS_API_KEY

Alpha Vantage API key used for market and news data.


Optional API Keys

STONKS_MASSIVE_API_KEY

Massive API key used to enable public-float data.

Float data is optional. STONKS continues to operate normally
when this key is not configured.


Optional Features

ENABLE_FLOAT_DATA

Controls whether Massive public-float data support is enabled.
Defaults to False.
```

## Documentation

### Subsystems

- [Journal Subsystem](docs/journal.md)
- [Historical Cache](docs/cache.md)
- [C.I.A. News Subsystem](docs/cia.md)

---

## License

```text
Personal educational project.
Acknowledgement Appreciated, but open source.
```
