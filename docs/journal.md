# Journal Subsystem

[← Back to Main README](../README.md)

The STONKS Journal subsystem records real and paper trading activity in a structured format for later review and analysis.

---

## Purpose

The Journal provides persistent trading records for individual orders and account value snapshots, keeping trading history separate from application source code.

---

## Features

- Trade order tracking
- Position-based order grouping
- Account value snapshots
- CSV-based persistence
- Journal CLI input and validation
- ZIP backup support

---

## Journal Data

Journal data is stored under:

```text
data/
└── journal/
    ├── orders.csv
    └── account_snapshots.csv
```

Journal data is stored outside the application source tree and is excluded from Git version control.

---

## Trade Orders

Launch the Journal CLI:

```powershell
.\scripts\journal.ps1
```

Select:

```text
1. Add Trade Order
```

A trade order records information such as:

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

The resulting record is stored in CSV format:

```csv
order_id,position_id,trade_date,ticker,order_type,fill_price,shares,order_total,time_issued,notes
1,1,2026-06-21,PLTR,BUY,4.02,645,2592.90,06:42,Opening position
```

---

## Position Tracking

Orders sharing the same `position_id` belong to the same trading position.

For example:

```text
Position #1

BUY   100 shares
BUY    50 shares
SELL   75 shares
SELL   75 shares
```

This allows multiple entries and exits to be associated with a single position and preserves scaling activity within the journal data.

---

## Account Snapshots

Account snapshots record changes in account value over time.

From the Journal CLI, select:

```text
2. Add Account Snapshot
```

Example:

```csv
snapshot_date,account_value_before,account_value_after,notes
2026-06-21,1000.00,1048.25,Good discipline
```

Account snapshots provide a historical record of account value independent of individual trade orders.

---

## Journal Backups

Create a journal backup with:

```powershell
.\scripts\backup_journal.ps1
```

Backups are written to:

```text
backups/
└── stonks_journal_2026-06-21_19-14-33.zip
```

The archive contains the journal CSV data:

```text
orders.csv
account_snapshots.csv
```

This provides a portable copy of the journal's persistent trading records.
