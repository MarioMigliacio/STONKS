# Journal Subsystem

[← Back to Main README](../README.md)

The STONKS Journal subsystem provides persistent storage, validation, and analytics for trading activity across multiple brokerage accounts.

The journal uses SQLite for structured data storage and separates database access, business logic, and financial analysis.

---

## Purpose

The Journal records trading activity and account-level cash transactions to support performance analysis, trading discipline, and historical review.

Its architecture is designed to support a future desktop graphical interface without coupling business logic to the user interface.

---

## Features

- SQLite database persistence (schema v2)
- Multiple trading account support
- Default account selection and account archival
- Position and trade execution tracking
- Partial entries and exits
- Deposits, withdrawals, and account-level transactions
- Position and account performance analytics
- Trading pattern analysis
- Repository and service architecture
- Account ownership validation
- Database integrity constraints
- SQLite database backup and restoration
- Human-readable CSV exports
- Automated regression testing

---

## Database Architecture

The Journal uses four primary SQLite tables.

| Table                  | Primary Key      | Purpose                                                      |
| ---------------------- | ---------------- | ------------------------------------------------------------ |
| `trading_accounts`     | `account_id`     | Brokerage account information                                |
| `positions`            | `position_id`    | Individual trading positions                                 |
| `trade_executions`     | `execution_id`   | BUY and SELL executions                                      |
| `account_transactions` | `transaction_id` | Deposits, withdrawals, and other account-level cash activity |

### Table Relationships

```text
trading_accounts
    |
    +---- positions
    |         |
    |         +---- trade_executions
    |
    +---- account_transactions
```

Each position belongs to one trading account.

Each trade execution belongs to one position and inherits its account association through that position.

Each account transaction belongs directly to one trading account.

The `transaction_id` and `execution_id` fields identify separate record types and do not reference each other.

### Storage

The SQLite database is stored outside the application source tree using the configured journal database path.

Runtime journal data is excluded from Git version control.

SQLite STRICT tables and foreign-key constraints help protect data integrity.

---

## Trading Accounts

Trading accounts represent individual brokerage accounts within the journal.

Supported account types include:

- Roth IRA
- Traditional IRA
- Cash
- Margin
- Other

Each account stores identifying information such as its name, account type, and optional broker.

### Default Accounts

The first active trading account automatically becomes the default.

The default account can be changed through the journal service.

Default changes are performed atomically to prevent inconsistent account selection.

### Account Archival

Accounts may be archived without deleting their historical records.

Archived accounts cannot receive new positions or account transactions and cannot become the default account.

A default account must be reassigned before it can be archived.

---

## Positions and Trade Executions

A position represents a trading opportunity associated with a ticker and trading account.

Positions may include strategy information, catalyst details, entry reasoning, and notes.

Each position can contain multiple trade executions.

For example:

```text
Position #1 — NVDA

BUY    100 shares
BUY     50 shares
SELL    75 shares
SELL    75 shares
```

This structure supports scaling into and out of positions while preserving individual execution history.

Each execution records information such as:

- Execution side (BUY or SELL)
- Execution timestamp
- Share quantity
- Execution price
- Trading fees

Financial quantities use Decimal-based calculations, with exact-value text storage in SQLite where applicable.

---

## Account Transactions

Account transactions represent cash activity separate from individual trades.

Examples include deposits and withdrawals.

Each transaction records:

- Trading account ownership
- Transaction type
- Transaction timestamp
- Amount
- Optional notes

Separating account transactions from trade executions allows trading performance to be evaluated independently of external cash contributions and withdrawals.

---

## Account Ownership and Integrity

Schema v2 requires positions and account transactions to belong to valid trading accounts.

Ownership is protected at multiple layers.

### Service Validation

The journal service rejects:

- Missing trading accounts
- Nonexistent trading accounts
- Archived accounts receiving new activity
- Attempts to reassign a position to another account

### Database Constraints

SQLite enforces:

- Required account ownership
- Foreign-key relationships
- Strict column typing
- Immutable position ownership
- Immutable account transaction ownership

Database triggers prevent ownership reassignment even when SQL operations bypass the journal service.

---

## Application Architecture

The Journal separates responsibilities into three primary layers.

### Models

Journal models represent trading accounts, positions, trade executions, and account transactions.

### Repository

`JournalRepository` manages database persistence and record retrieval.

It provides CRUD operations without containing user-interface logic.

### Service

`JournalService` coordinates journal operations, validates business rules, and manages transactional consistency.

Analytics components operate independently of the user interface.

This separation allows the future GUI to reuse the existing journal functionality.

---

## Journal Analytics

The journal includes analytical components for evaluating trading activity.

These support:

- Position-level trade analysis
- Realized trading performance
- Account-level performance calculations
- Trading pattern analysis

The architecture provides a foundation for future consolidated analytics across multiple brokerage accounts.

Portfolio-wide aggregation and inter-account transfer handling are planned for Phase B.

---

## Journal Backups

The Journal uses SQLite's native backup API to create consistent database backups.

Unlike the previous CSV-based backup system, SQLite backups preserve the database structure and its records.

Backups include:

- Trading accounts
- Positions
- Trade executions
- Account transactions
- Database indexes and triggers

### Backup Validation

Before restoration, STONKS verifies:

- The backup file exists
- SQLite integrity checks pass
- Required journal tables exist
- The schema version matches the supported version

### Restoration

Restoration creates a safety backup of the current database before replacing its contents.

The restored database is validated after the operation.

---

## CSV Exports

The Journal can export database records into human-readable CSV files.

Each export creates a timestamped directory containing:

```text
journal_YYYYMMDD_HHMMSS_ffffff/
├── trading_accounts.csv
├── positions.csv
├── trade_executions.csv
└── account_transactions.csv
```

CSV exports are intended for inspection, external analysis, and record portability.

**SQLite database backups remain the authoritative restoration format.**

---

## Testing

The Journal uses Pytest to verify database behavior and business rules.

Regression coverage includes:

- Database initialization and schema versioning
- Trading account creation and default selection
- Account archival restrictions
- Position and execution persistence
- Account transaction validation
- Financial analytics
- Account ownership enforcement
- Database foreign keys and triggers
- Backup creation, validation, and restoration
- CSV export functionality

Temporary SQLite databases isolate tests from production journal data.

---

## Development Status

**STONKS v2.1.0 — Trading Journal Revamp**

**Phase A: Multi-Account Foundation**

Implemented and regression-tested.

**Phase B: Combined Portfolio Intelligence**

Planned next, including consolidated account analytics and inter-account transfer handling.

**Desktop GUI**

Planned as a subsequent development stage.

The legacy CSV-based journal and command-line interface have been retired in favor of the SQLite architecture.
