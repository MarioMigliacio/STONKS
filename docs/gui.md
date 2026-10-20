# STONKS Desktop GUI

[← Back to Main README](../README.md)

The STONKS desktop interface provides a reusable **PySide6 application shell** and an interactive Trading Journal for managing brokerage accounts, positions, and trade executions. It is the GUI foundation introduced for **v2.1.0**.

The journal's database, financial calculations, and business rules remain separate from the user interface. The GUI uses the existing repository, service, and analytics components rather than implementing financial logic inside Qt widgets.

## Launching the desktop application

From the repository root, after initializing the environment and activating the virtual environment:

```powershell
.\scripts\init.ps1
.\scripts\activate.ps1
python -m stonks.gui.app
```

`stonks.gui.app` creates the Qt application, applies the dark theme, initializes the journal context, and opens the main window. The context closes its SQLite connection when the application exits.

**Note:** `python -m stonks` and `scripts/run.ps1` launch the stock scanner, not the desktop GUI. The GUI currently runs from the Python development environment.

## Interface overview

The main window contains a persistent navigation sidebar and a central page area implemented with `QStackedWidget`. Choosing a destination changes the central content without spawning another console or a new main application window.

| Navigation destination | Current functionality                                                                                          |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Trading Journal**    | Positions overview, performance metrics, search and status filters, position management, and execution details |
| **Trading Accounts**   | Account creation, editing, default selection, archival, reactivation, and guarded deletion                     |
| **Dashboard**          | Placeholder for future functionality                                                                           |
| **Market Scanner**     | Placeholder in the desktop GUI; the existing scanner remains available separately                              |
| **C.I.A.**             | Placeholder in the desktop GUI; existing catalyst tools remain available separately                            |

### Trading accounts

The **Trading Accounts** page lists account name, type, broker, active/archived status, and default designation.

- Select **New Account** to register a brokerage account.
- Select an account and use **Actions** to edit its details or make an eligible active account the default.
- Archive an eligible non-default account to retain its history while preventing new activity.
- Reactivate an archived account when it needs to become active again.
- Permanent account deletion is a guarded operation with an explicit confirmation dialog and backend integrity checks; use archival when history must be retained.

Archived accounts remain available for historical review. Account and position activity in the GUI is restricted by account status, and the journal service applies its own validation independently of button availability.

### Trading Journal: positions overview

Select **Trading Journal** in the sidebar. The overview contains:

- A **Trading Account** selector that scopes the table to one account.
- A **Search ticker** field for case-insensitive substring matching.
- A **Status** selector for All Statuses, Draft, Open, or Closed.
- A performance table showing **Ticker**, **Status**, **Shares**, **Realized P&L**, and **Return %**.
- A **New Position** action and an **Actions** menu for the selected position.

Search and status filters can be combined. They remain selected when switching accounts, allowing the same ticker or status to be inspected across accounts. A no-match message is distinct from an account with no positions. Actions are disabled when a position is no longer eligible for editing or deletion.

#### Creating and editing positions

Use **New Position** to record a ticker and optional trading context, such as strategy, catalyst, entry reason, and notes. The edit dialog also supports reflection fields such as exit reason, mistakes, and lessons learned.

Select a row and open **Actions → Edit Position** to change its metadata. **Delete Position** is available only for a position with no executions, subject to account-status and service validation. Positions with trade history must retain that history rather than being deleted through this action.

### Position details and executions

Double-click a position row to open its **Position Details** dialog. This view displays position metadata, performance cards, and a chronological execution table.

For an eligible active account, use **Add Execution** to record a BUY or SELL fill. Each execution includes a date/time, share quantity, price, fees, and optional notes. Select an execution and use **Actions** to edit or delete it; deletions require confirmation.

Trade quantities and prices are handled with `Decimal` values. The journal service validates writes, including chronology and overselling safeguards. Changes made in Position Details are reflected in the overview when the dialog closes.

Archived account positions and executions can still be inspected, but mutation controls are disabled.

## Understanding the performance metrics

The position overview and details are powered by `calculate_position_metrics()` in the journal analytics package.

| Metric                   | Meaning                                                                       |
| ------------------------ | ----------------------------------------------------------------------------- |
| **Draft**                | Position with no trade executions                                             |
| **Open**                 | Position with shares remaining                                                |
| **Closed**               | Position whose purchased shares have been fully sold                          |
| **Remaining Shares**     | Quantity currently held, accounting for recorded buys and sells               |
| **Avg Buy Price**        | Historical share-weighted average of BUY execution prices (excluding fees)    |
| **Realized P&L**         | Profit or loss on sold shares, incorporating allocated trading costs and fees |
| **Realized Return**      | Realized P&L as a percentage of cost basis allocated to shares sold           |
| **Remaining Cost Basis** | Recorded cost basis still assigned to open shares                             |

The analytics use a weighted-average cost approach. Realized performance is calculated from the journal's **recorded executions**, not live market quotes. **Unrealized P&L and current market-value equity are not displayed** in these views. Return percentage may be unavailable until shares have been sold.

For account-level and consolidated portfolio analytics provided by the backend, see [Journal Subsystem](journal.md).

## Architecture and source layout

```text
src/stonks/
├── gui/
│   ├── app.py                   # QApplication startup and journal lifecycle
│   ├── main_window.py           # QMainWindow and stacked-page navigation
│   ├── icons.py                 # SVG icon loading
│   ├── assets/                  # GUI icon resources
│   ├── navigation/              # Persistent navigation sidebar
│   ├── pages/                   # Account, position, execution, placeholder pages/dialogs
│   ├── styles/theme.py          # STONKS_DARK_THEME Qt stylesheet
│   └── widgets/                 # Reusable position metrics presentation
└── journal/
    ├── journal_context.py      # Shared connection, repository, and service
    ├── analytics/              # Financial calculations
    ├── models/                 # Journal entities and enums
    ├── persistence/            # SQLite and repositories
    ├── services/               # Validated, transactional writes
    ├── validation/             # Journal integrity rules
    └── export/                 # CSV export support
```

### Dependency and event flow

```text
QApplication (gui/app.py)
    └── JournalContext
          ├── JournalRepository
          └── JournalService
                ↓
         MainWindow / QStackedWidget
                ├── AccountsPage
                └── PositionsPage
                       └── PositionDetailsDialog
                              └── Execution dialogs

GUI reads → repository / analytics
GUI writes → journal service → repository / SQLite
```

`JournalContext` owns the SQLite connection, creates the repository and service, and ensures cleanup. `MainWindow` passes these dependencies into the functional pages. The GUI does not open independent database connections per dialog.

`NavigationSidebar` emits page identifiers, and `MainWindow` selects the appropriate page in `QStackedWidget`. Returning to the Trading Journal refreshes its account selector so changes made on the Accounts page are visible without restarting the application.

### Styling and icons

`STONKS_DARK_THEME` in `gui/styles/theme.py` defines the global dark palette and named widget styles through Qt Style Sheets (QSS). Widgets use `objectName` values for targeted selectors such as journal controls, danger confirmations, and position metric cards.

`gui/icons.py` loads SVG assets for Qt actions and buttons. Keep icon references and their corresponding resource files aligned when introducing new actions. Positive and negative performance are visually differentiated; financial meaning must remain available through the displayed numbers and signs, not color alone.

New pages should reuse the existing shell and domain services rather than introducing a parallel window, database layer, or separate financial calculation path.

## Testing and development

GUI tests use **pytest** and **pytest-qt**. Existing coverage exercises account and position selection, create/edit/delete workflows, execution operations, read-only restrictions, performance displays, and filtering behavior. Journal backend tests independently exercise persistence, service validation, and analytics.

From the repository root:

```powershell
.\scripts\lint.ps1
.\scripts\test.ps1
```

For focused GUI work:

```powershell
python -m pytest tests/gui/ -v
```

GUI tests should use temporary journal databases so they cannot modify personal trading data. Functional interface changes should be checked against the service and analytics behavior, with a short visual smoke test for purely cosmetic QSS adjustments.

---
