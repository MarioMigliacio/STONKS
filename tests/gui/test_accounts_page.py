# =============================================================================
# File: test_accounts_page.py
# Purpose: Pytest file for test_accounts_page.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from stonks.gui.pages.accounts_page import AccountsPage
from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.gui.pages.delete_account_dialog import DeleteAccountDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount


def _create_archived_account_page(qtbot, journal):
    """
    Create an Accounts page with a selectable archived account.

    Args:
        qtbot:
            Pytest-qt widget fixture.

        journal:
            Initialized journal application context.

    Returns:
        tuple:
            Accounts page, default account ID, and archived account ID.
    """
    default_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

    archived_id = journal.m_service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

    assert journal.m_service.archive_trading_account(archived_id)

    page = AccountsPage(
        repository=journal.m_repository,
        service=journal.m_service,
    )
    qtbot.addWidget(page)

    for row in range(page.m_table.rowCount()):
        item = page.m_table.item(row, 0)

        if item.data(Qt.UserRole) == archived_id:
            page.m_table.selectRow(row)
            break

    assert page.get_selected_account_id() == archived_id

    return page, default_id, archived_id


def test_accounts_page_displays_database_records(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the accounts page displays stored trading accounts."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_connection.execute(
            """
            INSERT INTO trading_accounts (
                name,
                account_type,
                broker
            )
            VALUES (?, ?, ?)
            """,
            ("Retirement Account", "ROTH_IRA", "Webull"),
        )

        journal.m_connection.commit()

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.rowCount() == 1

        assert page.m_table.item(0, 0).text() == "Retirement Account"
        assert page.m_table.item(0, 1).text() == "Roth Ira"
        assert page.m_table.item(0, 2).text() == "Webull"
        assert page.m_table.item(0, 3).text() == "Active"


def test_accounts_page_handles_empty_database(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the accounts page handles an empty journal."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.rowCount() == 0


def test_accounts_page_displays_default_account(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the default trading account is identified in the table."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        assert page.m_table.columnCount() == 5
        assert page.m_table.rowCount() == 2

        assert page.m_table.item(0, 4).text() == "★ Yes"
        assert page.m_table.item(1, 4).text() == "—"


def test_accounts_page_returns_selected_account_id(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify account selection returns the database identifier."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        assert page.get_selected_account_id() == account_id


def test_accounts_page_preserves_selection_on_refresh(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify refreshing account data preserves the selected account."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(journal.m_repository)
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        page.refresh_accounts()

        assert page.get_selected_account_id() == account_id


def test_accounts_page_edit_persists_changes(
    qtbot,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify editing an account updates SQLite and refreshes the table."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        def accept_edit(dialog):
            dialog.m_name.setText("Updated Cash Account")
            dialog.m_broker.setText("Updated Broker")
            return QDialog.Accepted

        monkeypatch.setattr(
            CreateAccountDialog,
            "exec",
            accept_edit,
        )

        page.m_edit_action.trigger()

        stored_account = journal.m_repository.get_trading_account(account_id)

        assert stored_account is not None
        assert stored_account.name == "Updated Cash Account"
        assert stored_account.broker == "Updated Broker"
        assert stored_account.is_default is True

        assert page.m_table.item(0, 0).text() == "Updated Cash Account"
        assert page.get_selected_account_id() == account_id


def test_accounts_page_edit_cancelled(
    qtbot,
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify canceling an edit leaves the trading account unchanged."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        monkeypatch.setattr(
            CreateAccountDialog,
            "exec",
            lambda dialog: QDialog.Rejected,
        )

        page.m_edit_action.trigger()

        stored_account = journal.m_repository.get_trading_account(account_id)

        assert stored_account is not None
        assert stored_account.name == "Webull Cash"
        assert stored_account.broker == "Webull"


def test_accounts_page_switches_default_account(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify the selected account becomes the new default."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        roth_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        # Select the second account.
        page.m_table.selectRow(1)

        assert page.m_default_action.isEnabled()

        # Trigger the same QAction used by the menu.
        page.m_default_action.trigger()

        roth = journal.m_repository.get_trading_account(roth_id)
        cash = journal.m_repository.get_trading_account(cash_id)

        assert roth.is_default is False
        assert cash.is_default is True

        # Verify the visible table reflects the change.
        assert page.m_table.item(0, 4).text() == "—"
        assert page.m_table.item(1, 4).text() == "★ Yes"

        # Account selection should remain unchanged.
        assert page.get_selected_account_id() == cash_id

        # The new default can no longer trigger the action.
        assert not page.m_default_action.isEnabled()


def test_default_action_disabled_for_current_default(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify an existing default account cannot be selected again."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
                broker="Webull",
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        assert page.m_actions_button.isEnabled()
        assert not page.m_default_action.isEnabled()


def test_default_switch_persists_after_reopening(
    qtbot,
    tmp_path: Path,
) -> None:
    """Verify default account changes persist across database sessions."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(1)
        page.m_default_action.trigger()

    # Reopen the database in a new application context.
    with JournalContext(database_path) as reopened:
        default_account = reopened.m_repository.get_default_trading_account()

        assert default_account is not None
        assert default_account.account_id == cash_id


def test_archive_account_preserves_account_record(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify confirmed archival makes an account inactive."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        # Find the account by ID, not by assumed row order.
        for row in range(page.m_table.rowCount()):
            item = page.m_table.item(row, 0)

            if item.data(Qt.UserRole) == cash_id:
                page.m_table.selectRow(row)
                break

        assert page.get_selected_account_id() == cash_id
        assert page.m_archive_action.isEnabled()

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.Yes,
        )

        page.m_archive_action.trigger()

        archived_account = journal.m_repository.get_trading_account(cash_id)

        assert archived_account is not None
        assert archived_account.is_active is False
        assert archived_account.is_default is False

        assert page.m_table.item(page.m_table.currentRow(), 3).text() == "Archived"

        assert not page.m_archive_action.isEnabled()
        assert not page.m_default_action.isEnabled()


def test_archive_account_cancellation_preserves_state(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify declining archival leaves the account active."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Roth IRA",
                account_type=AccountType.ROTH_IRA,
            )
        )

        cash_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Webull Cash",
                account_type=AccountType.CASH,
            )
        )

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        for row in range(page.m_table.rowCount()):
            item = page.m_table.item(row, 0)

            if item.data(Qt.UserRole) == cash_id:
                page.m_table.selectRow(row)
                break

        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.No,
        )

        page.m_archive_action.trigger()

        account = journal.m_repository.get_trading_account(cash_id)

        assert account is not None
        assert account.is_active is True


def test_reactivate_account_action(
    qtbot,
    tmp_path,
) -> None:
    """Verify archived accounts can be reactivated through the GUI."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(
            TradingAccount(
                name="Roth IRA",
                account_type=AccountType.ROTH_IRA,
            )
        )

        account_id = journal.m_service.create_trading_account(
            TradingAccount(
                name="Cash Account",
                account_type=AccountType.CASH,
            )
        )

        journal.m_service.archive_trading_account(account_id)

        page = AccountsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )

        qtbot.addWidget(page)

        for row in range(page.m_table.rowCount()):
            item = page.m_table.item(row, 0)

            if item.data(Qt.UserRole) == account_id:
                page.m_table.selectRow(row)
                break

        assert page.get_selected_account_id() == account_id

        assert not page.m_archive_action.isVisible()
        assert page.m_reactivate_action.isVisible()
        assert page.m_reactivate_action.isEnabled()

        page.m_reactivate_action.trigger()

        account = journal.m_repository.get_trading_account(account_id)

        assert account is not None
        assert account.is_active is True
        assert account.is_default is False

        assert page.m_archive_action.isVisible()
        assert not page.m_reactivate_action.isVisible()


def test_delete_account_cancellation_does_not_delete(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify cancelling deletion never calls the deletion service."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        page, _, archived_id = _create_archived_account_page(
            qtbot,
            journal,
        )

        deletion_calls = []

        def track_deletion(account_id):
            deletion_calls.append(account_id)
            return True

        monkeypatch.setattr(
            journal.m_service,
            "delete_trading_account",
            track_deletion,
        )

        monkeypatch.setattr(
            DeleteAccountDialog,
            "exec",
            lambda self: QDialog.Rejected,
        )

        page.m_delete_action.trigger()

        assert deletion_calls == []

        account = journal.m_repository.get_trading_account(archived_id)

        assert account is not None
        assert account.is_active is False


def test_confirmed_account_deletion_removes_selected_account(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify confirmed deletion removes only the selected account."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        page, default_id, archived_id = _create_archived_account_page(
            qtbot,
            journal,
        )

        # Dialog authorization is tested separately.
        # Here we test the page-to-service integration.
        monkeypatch.setattr(
            DeleteAccountDialog,
            "exec",
            lambda self: QDialog.Accepted,
        )

        assert page.m_delete_action.isEnabled()

        page.m_delete_action.trigger()

        assert journal.m_repository.get_trading_account(archived_id) is None

        default_account = journal.m_repository.get_trading_account(default_id)

        assert default_account is not None
        assert default_account.is_default is True

        # The deleted account should disappear from the table.
        displayed_ids = [page.m_table.item(row, 0).data(Qt.UserRole) for row in range(page.m_table.rowCount())]

        assert archived_id not in displayed_ids
        assert default_id in displayed_ids


def test_delete_dialog_receives_correct_record_counts(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify deletion confirmation receives live financial record counts."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        page, _, archived_id = _create_archived_account_page(
            qtbot,
            journal,
        )

        # Temporarily reactivate the account to create test records.
        assert journal.m_service.reactivate_trading_account(archived_id)

        position_id = journal.m_service.create_position(
            Position(
                ticker="NVDA",
                account_id=archived_id,
            )
        )

        timestamp = datetime(
            2026,
            10,
            15,
            14,
            30,
            tzinfo=timezone.utc,
        )

        journal.m_service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=timestamp,
                shares=Decimal("10"),
                price=Decimal("150"),
            )
        )

        journal.m_service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.SELL,
                executed_at=timestamp,
                shares=Decimal("10"),
                price=Decimal("155"),
            )
        )

        journal.m_service.create_account_transaction(
            AccountTransaction(
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=timestamp,
                amount=Decimal("2000"),
                account_id=archived_id,
            )
        )

        # Archive again now that the test data exists.
        assert journal.m_service.archive_trading_account(archived_id)

        page.refresh_accounts()

        captured = {}

        class RecordingDeleteDialog:
            """Capture dialog arguments without displaying a modal window."""

            def __init__(self, account_name, summary, parent=None):
                captured["account_name"] = account_name
                captured["summary"] = summary

            def exec(self):
                return QDialog.Rejected

        monkeypatch.setattr(
            "stonks.gui.pages.accounts_page.DeleteAccountDialog",
            RecordingDeleteDialog,
        )

        page.m_delete_action.trigger()

        assert captured["account_name"] == "Old Cash"

        assert captured["summary"] == {
            "positions": 1,
            "executions": 2,
            "transactions": 1,
        }

        # Rejecting the dialog leaves the data untouched.
        assert journal.m_repository.get_trading_account(archived_id) is not None
