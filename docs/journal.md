# Journal Subsystem

[← Back to Main README](../README.md)

The STONKS Journal subsystem is designed to track real and paper trades in a structured format for later analysis and reporting.

---

## Purpose

The Journal subsystem was created to help traders collect objective performance data, identify strengths and weaknesses, and make decisions based on measurable results rather than emotions or memory.

---

## Features

- Record individual trade orders
- Record account value snapshots
- CSV-based storage for simplicity and transparency
- Automatic data validation through the Journal CLI
- Backup and recovery support through ZIP archives
- Foundation for future analytics and reporting

---

## Journal Data Storage

Journal data is stored outside of source code to keep runtime data separate from application logic.

```text
data/
└── journal/
    ├── orders.csv
    └── account_snapshots.csv
```

Journal files are intentionally excluded from Git version control.

---

## Adding Trade Orders

Launch the journal CLI:

```powershell
.\scripts\journal.ps1
```

Select:

```text
1. Add Trade Order
```

Example:

```text
Order ID: 1
Position ID: 1
Ticker: PLTR
Order Type (BUY/SELL): BUY
Fill Price: 4.02
Shares: 645
Time Issued: 06:42
Notes: Opening position
```

Generated CSV:

```csv
order_id,position_id,trade_date,ticker,order_type,fill_price,shares,order_total,time_issued,notes
1,1,2026-06-21,PLTR,BUY,4.02,645,2592.90,06:42,Opening position
```

---

## Position Tracking

A position may contain multiple orders.

Example:

```text
Position #1

BUY  100 shares
BUY   50 shares
SELL  75 shares
SELL  75 shares
```

This allows STONKS to support:

- Scaling into positions
- Scaling out of positions
- Average entry calculations
- Average exit calculations
- Position-level profit and loss

---

## Account Snapshots

Account snapshots track account growth over time.

Select:

```text
2. Add Account Snapshot
```

Example CSV:

```csv
snapshot_date,account_value_before,account_value_after,notes
2026-06-21,1000.00,1048.25,Good discipline
```

Future analytics can calculate:

- Daily account growth
- Account equity curves
- Percentage returns
- Performance trends

---

## Journal Backups

Create a backup:

```powershell
.\scripts\backup_journal.ps1
```

Result:

```text
backups/
└── stonks_journal_2026-06-21_19-14-33.zip
```

Backup archives contain:

```text
orders.csv
account_snapshots.csv
```

This protects trading history and journal data from accidental loss.

---

## Future Roadmap

Planned journal enhancements:

- Position profit/loss calculations
- Win/loss statistics
- Average hold time analysis
- Best and worst ticker reports
- Profit factor calculations
- Journal analytics dashboard
- GUI integration
- Optional SQLite backend
