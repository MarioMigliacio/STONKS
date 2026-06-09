# STONKS 🚀

Author: Mario Migliacio, 2026

STONKS is a personal stock scanner and paper trading companion project focused on learning:

- Python development
- market scanners
- momentum trading concepts
- API integration
- financial data analysis

This project is inspired by momentum day trading strategies and is intended for:

- educational purposes
- simulation trading
- personal experimentation

---

# Goals

- Build a custom stock scanner
- Learn Python through practical development
- Integrate market/news APIs
- Track relative volume, gaps, float, and momentum
- Eventually create a lightweight GUI dashboard

---

# Current Features

- Alpha Vantage API integration
- Intraday stock data retrieval
- Volume filtering
- Modular Python package structure

---

# Planned Features

- Relative volume scanner
- Gap percentage scanner
- Float tracking
- News catalyst integration
- Async API requests
- GUI dashboard
- Watchlists and alerts
- Data journal for real record analysis and insights
- _Note_ Real data is kept in data/journal, but the template files are committed to project. Assumes you maintain your own personal files:
    - account_snapshots.csv
    - orders.csv

---

# Journal Subsystem

- data/journal/orders.csv
    - Stores individual trade orders.

- data/journal/account_snapshots.csv
    - Stores account value snapshots.

- journal_storage.py
    - Responsible for persistence.

- journal_analyzer.py
    - Responsible for statistics and reporting.

- trade_order.py
    - A TradeOrder represents one filled buy or sell order.

- account_snapshot.py
    - Account snapshots represent portfolio/account state at a point in time.

---

# Tech Stack

- Python
- requests
- pandas
- Alpha Vantage API

---

# How To Get started

```
- on a terminal, create and cd into a directory to house the repo.
- run git clone https://github.com/MarioMigliacio/STONKS.git
- cd into STONKS/
- run ".\script\init.ps1"
- run ".\venv\Scripts\activate"
- run pip install requests pandas python-dotenv

- visit https://www.alphavantage.co/support/# 'Claim your API key' and update .env file as described in init.ps1
- run project with python -m stonks ( outside src/ )
- . . .
- profit
```

---

# Project Structure

```text
STONKS/
├── data
│   └── journal
│       └── templates
├── scripts/
├── src/
│   └── stonks/
│       ├── api/
|       ├── config/
│       ├── journal/
|       ├── models/
|       └── scanner/
|
├── README.md
├── .env (secret)
└── venv/
```

---
