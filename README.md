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

The project combines market scanning, public-float analysis, catalyst intelligence, historical data caching, and a PySide6 desktop Trading Journal to support data-driven trading decisions and disciplined trade review.

---

## Current Features

### Desktop Trading Journal (PySide6)

- Reusable `QMainWindow` application shell with persistent sidebar navigation and stacked pages
- Dark theme and SVG icons
- Trading account creation, editing, default selection, archival, reactivation, and guarded permanent deletion
- Account-scoped position creation, editing, deletion, and detailed review
- BUY/SELL execution entry, editing, deletion, and chronological history
- Position analytics: Draft/Open/Closed status, remaining shares, historical average buy price, cost basis, realized P&L, and realized return
- Live ticker search and position-status filters
- Read-only historical access to archived trading accounts
- Shared `JournalContext`, repository, and service layers; financial calculations remain separate from the GUI

The Trading Journal, Trading Accounts, Market Scanner, and C.I.A. desktop pages are functional. Dashboard remains a placeholder.

Account Details provides opening cash snapshots, deposits, withdrawals, fees, adjustments, dated transaction history, and linked internal transfers. Transfers update both account ledgers atomically and are excluded from external contribution totals. The GUI also displays opening-aware account performance metrics.

See the [Desktop GUI Guide](docs/gui.md) for workflows and architecture, and the [Journal Subsystem](docs/journal.md) for persistence, accounting, and backend behavior.

### Journal Backend

- SQLite-based persistence (schema v3), with multi-account ownership and integrity rules
- Roth IRA, Traditional IRA, Cash, Margin, and Other account types
- Position and trade-execution history, including partial entries and exits
- Account transactions for deposits, withdrawals, fees, adjustments, and atomic linked transfers.
- Dated opening cash snapshots and chronological cash safeguards.
- Weighted-average position cost and realized P&L analytics
- Account cash-flow, performance, and consolidated portfolio analytics
- Repository, service, validation, and analytics architecture
- Managed SQLite lifecycle, native database backups and restoration, and CSV exports

The legacy journal CLI has been retired in favor of the desktop interface.

### Scanner

- Live quote retrieval
- Change % and Gap % calculations
- Relative Volume (RVOL) and historical volume analysis
- Public-float data enrichment, turnover, and float-size classification
- Scanner candidate model and configurable volume filtering

The desktop Scanner Workspace supports strategy selection, ANY/ALL matching, background execution, cooperative cancellation, status feedback, and a results table. see [Scanner Workspace](docs/scanner_workspace.md).

### Float Data

- Public-float data provided by Massive
- Float share and float percentage reporting
- Effective-date tracking and local caching
- Configurable expiration and graceful fallback when enrichment is unavailable

See [Float Data](docs/float_data.md).

### Price Action

- Historical intraday candle retrieval through Massive
- 1-minute, 5-minute, 15-minute, 30-minute, 60-minute, and daily timeframes
- Pre-market, regular-session, and after-hours candle selection
- Regular-session change, high, low, and range analysis
- Configurable lookbacks, scanner enrichment, and cache-first access
- Historical price-action CLI

See [Price Action](docs/price_action.md).

### C.I.A. — Catalyst Intelligence Analysis

- Ticker-specific Marketaux news retrieval through a provider-independent service
- Normalized article evidence and duplicate filtering
- Catalyst classification, freshness, strength, confidence, and sentiment
- Mission Brief with active and historical intelligence
- Supporting Intelligence article table and navigable Article Dossier
- Background analysis, failure-state preservation, and original publisher links

See [C.I.A. News Subsystem](docs/cia.md).

### Caching and Development

- Historical market-data, intraday candle, and public-float caching
- Configurable cache expiration where applicable
- Pytest and pytest-qt regression testing
- Ruff linting and formatting, PowerShell helpers, and GitHub Actions checks
- Environment-based API key configuration and structured application logging

See [Historical Cache](docs/cache.md).

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
├── docs/
├── scripts/
├── src/
│   └── stonks/
│       ├── api/
│       │   └── providers/
│       ├── cache/
│       ├── cia/
│       ├── config/
│       ├── gui/
│       │   ├── assets/
│       │   ├── navigation/
│       │   ├── pages/
│       │   ├── styles/
│       │   ├── widgets/
│       │   └── workers/
│       ├── journal/
│       │   ├── analytics/
│       │   ├── export/
│       │   ├── models/
│       │   ├── persistence/
│       │   ├── services/
│       │   └── validation/
│       ├── models/
│       ├── news/
│       └── scanner/
├── tests/
│   ├── api/
│   ├── cache/
│   ├── cia/
│   ├── gui/
│   ├── journal/
│   └── scanner/
├── venv/
├── .env
├── pyproject.toml
├── README.md
└── requirements.txt
```

Local virtual environments, database files, caches, logs, and backups are runtime artifacts and should not be committed to source control.

---

## Getting Started (Windows / PowerShell)

Clone the repository:

```powershell
git clone https://github.com/MarioMigliacio/STONKS.git
cd STONKS
```

Initialize the environment and install dependencies:

```powershell
.\scripts\init.ps1
```

Activate the environment in your working PowerShell session:

```powershell
.\scripts\activate.ps1
```

The activation script sets `PYTHONPATH=src`. The project dependencies include PySide6 and pytest-qt.

For market API functionality, configure the `.env` file created from `.env.example`:

```text
STONKS_API_KEY=your_api_key
STONKS_MASSIVE_API_KEY=your_api_key
STONKS_MARKETAUX_API_KEY=your_marketaux_api_key
```

The desktop CIA workspace uses Marketaux, Massive supports float/aggregate candle features, and `STONKS_API_KEY` supports Alpha Vantage market features.

Float enrichment is controlled by `ENABLE_FLOAT_DATA` in the application settings; it defaults to `False`.

---

## Usage

### Desktop Application

Launch STONKS using:

```powershell
.\scripts\run.ps1
```

Or, after activating the environment: `python -m stonks`

The GUI initializes its journal database and repository/service dependencies, applies the dark stylesheet, and opens the desktop shell.

1. Open **Trading Accounts** to create an account and set or change the default account.
2. Double-click an account to open **Account Details**, where you can set opening cash, record account transactions, and manage linked transfers.
3. Open **Trading Journal** and select the trading account.
4. Create a position, then double-click it to view its details and record BUY/SELL executions.
5. Double-click a trade execution in **Position Details** to edit it, or use its Actions menu.
6. Review realized performance, search by ticker, and filter positions by Draft, Open, or Closed status.

Archived accounts remain viewable but are not editable. Dashboard remains a placeholder; Scanner and C.I.A. are functional desktop workspaces.

### Scanner

Open Scanner in the desktop sidebar, select Standard Market Scanner, and click Run Scan. Cancel requests cooperative cancellation. API-enabled runs consume provider requests. The existing CLI is still available using `python -m stonks.scanner_cli` after activating the environment.

### C.I.A. Workspace

Open C.I.A. from the desktop sidebar, enter a ticker, and select Analyze Ticker. Review the Mission Brief and Supporting Intelligence, then open an article dossier for details or the publisher URL. A Marketaux API key is required for live news retrieval. See [C.I.A.](docs/cia.md) and [Desktop GUI Guide](docs/gui.md).

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

### Tests and Quality Checks

```powershell
.\scripts\test.ps1
.\scripts\lint.ps1
```

Run focused tests:

```powershell
.\scripts\test.ps1 -Target gui
.\scripts\test.ps1 -Target journal
.\scripts\test.ps1 -Path tests/test_entry_points.py

additional options include:

.\scripts\test.ps1 -Mode Quick
.\scripts\test.ps1 -FailFast
.\scripts\test.ps1 -Profile
```

Apply formatting fixes when needed:

```powershell
.\scripts\format.ps1
```

Clean generated artifacts or caches:

```powershell
.\scripts\clean.ps1
.\scripts\clear_cache.ps1
```

---

## Configuration and Data

The journal database is stored by default at `data/journal/stonks_journal.db`, as configured in `src/stonks/config/journal_paths.py`. Application data should be backed up before destructive changes or restoration.

SQLite backup/restore and CSV export support are implemented in the backend. A complete desktop workflow for account transactions and data lifecycle management remains part of release integration.

Account and portfolio cash calculations use a saved dated opening cash snapshot when present. Events before that snapshot do not change reconstructed cash; without a snapshot, cash starts from an unverified zero assumption. Contributions and realized P&L retain their all-record history. Equity at cost basis is not live market equity. **Equity at cost basis is not live market equity**; unrealized price changes are not included. See the [Journal Subsystem](docs/journal.md) for financial definitions and limitations.

---

## Documentation

- [Desktop GUI Guide](docs/gui.md)
- [Journal Subsystem](docs/journal.md)
- [Historical Cache](docs/cache.md)
- [C.I.A. News Subsystem](docs/cia.md)
- [Float Data](docs/float_data.md)
- [Price Action](docs/price_action.md)
- [Scanner Workspace](docs/scanner_workspace.md)

---

## License

```text
Personal educational project.

Acknowledgement appreciated, but open source.
```
