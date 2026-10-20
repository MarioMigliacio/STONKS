"""GUI and backend regression tests for Account Details & Transactions."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.account_details_dialog import AccountDetailsDialog
from stonks.gui.pages.account_transaction_dialog import AccountTransactionDialog
from stonks.gui.pages.accounts_page import AccountsPage
from stonks.gui.pages.delete_account_transaction_dialog import DeleteAccountTransactionDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount


@pytest.fixture
def account_details(qtbot, tmp_path):
    """Provide a functional account-detail dialog over an isolated SQLite DB."""
    with JournalContext(tmp_path / "journal.db") as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
        dialog = AccountDetailsDialog(account_id, journal.m_repository, journal.m_service)
        qtbot.addWidget(dialog)
        yield journal, account_id, dialog


def make_transaction(account_id, kind, amount, notes=""):
    """Build an example non-trade transaction with a UTC timestamp."""
    return AccountTransaction(
        transaction_type=kind,
        occurred_at=datetime(2026, 10, 19, 15, 0, tzinfo=timezone.utc),
        amount=Decimal(amount),
        account_id=account_id,
        notes=notes,
    )


def visible_types(dialog):
    """Return transaction types currently visible in the ledger table."""
    return [
        dialog.m_table.item(row, 1).text()
        for row in range(dialog.m_table.rowCount())
        if not dialog.m_table.isRowHidden(row)
    ]


def test_account_details_shows_backend_metrics(account_details):
    """Verify the ledger and account metrics use persisted transactions."""
    journal, account_id, dialog = account_details
    journal.m_service.create_account_transaction(make_transaction(account_id, AccountTransactionType.DEPOSIT, "5000"))
    journal.m_service.create_account_transaction(make_transaction(account_id, AccountTransactionType.FEE, "10"))
    dialog.refresh_details()
    assert dialog.m_table.rowCount() == 2
    assert dialog.m_metrics.m_cash_balance.text() == "$4,990.00"
    assert dialog.m_metrics.m_contributions.text() == "$5,000.00"
    assert dialog.m_metrics.m_realized_pnl.text() == "-$10.00"


def test_account_details_filters_by_type_and_notes(account_details):
    """Verify type selection and free-text query combine correctly."""
    journal, account_id, dialog = account_details
    journal.m_service.create_account_transaction(
        make_transaction(account_id, AccountTransactionType.DEPOSIT, "1000", "Opening cash")
    )
    journal.m_service.create_account_transaction(
        make_transaction(account_id, AccountTransactionType.FEE, "5", "Account maintenance")
    )
    dialog.refresh_details()
    dialog.m_search_input.setText("account")
    assert visible_types(dialog) == ["Fee"]
    deposit_index = dialog.m_type_filter.findData("DEPOSIT")
    dialog.m_type_filter.setCurrentIndex(deposit_index)
    assert visible_types(dialog) == []
    assert not dialog.m_empty_label.isHidden()
    dialog.m_search_input.clear()
    assert visible_types(dialog) == ["Deposit"]


def test_account_details_filters_clear_selected_actions(account_details):
    """Verify hidden transactions cannot remain selected for mutation."""
    journal, account_id, dialog = account_details
    journal.m_service.create_account_transaction(make_transaction(account_id, AccountTransactionType.DEPOSIT, "1000"))
    dialog.refresh_details()
    dialog.m_table.selectRow(0)
    assert dialog.m_actions_button.isEnabled()
    dialog.m_search_input.setText("fee")
    assert dialog.get_selected_transaction_id() is None
    assert not dialog.m_edit_action.isEnabled()
    assert not dialog.m_delete_action.isEnabled()


def test_account_details_creates_transaction(account_details, monkeypatch):
    """Verify the Add Transaction action persists and refreshes the ledger."""
    journal, account_id, dialog = account_details

    def accept_transaction(form):
        form.m_type.setCurrentIndex(form.m_type.findData("DEPOSIT"))
        form.m_amount.setText("125.50")
        return QDialog.Accepted

    monkeypatch.setattr(AccountTransactionDialog, "exec", accept_transaction)
    dialog.m_add_button.click()
    saved = journal.m_repository.get_account_transactions(account_id)
    assert len(saved) == 1
    assert saved[0].amount == Decimal("125.50")
    assert dialog.m_table.rowCount() == 1


def test_account_details_edits_and_deletes_transaction(account_details, monkeypatch):
    """Verify selected row operations preserve identity and require confirmation."""
    journal, account_id, dialog = account_details
    transaction_id = journal.m_service.create_account_transaction(
        make_transaction(account_id, AccountTransactionType.DEPOSIT, "100")
    )
    dialog.refresh_details()
    dialog.m_table.selectRow(0)

    def edit_transaction(form):
        form.m_amount.setText("200")
        return QDialog.Accepted

    monkeypatch.setattr(AccountTransactionDialog, "exec", edit_transaction)
    dialog.m_edit_action.trigger()
    assert journal.m_repository.get_account_transaction(transaction_id).amount == Decimal("200")
    assert dialog.get_selected_transaction_id() == transaction_id

    monkeypatch.setattr(DeleteAccountTransactionDialog, "exec", lambda self: QDialog.Accepted)
    dialog.m_delete_action.trigger()
    assert journal.m_repository.get_account_transaction(transaction_id) is None
    assert dialog.m_table.rowCount() == 0


def test_archived_account_details_are_read_only(account_details):
    """Verify archived accounts show ledger data but disable writes."""
    journal, account_id, dialog = account_details
    transaction_id = journal.m_service.create_account_transaction(
        make_transaction(account_id, AccountTransactionType.DEPOSIT, "100")
    )
    other_id = journal.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
    journal.m_service.set_default_trading_account(other_id)
    journal.m_service.archive_trading_account(account_id)
    dialog.refresh_details()
    dialog.m_table.selectRow(0)
    assert not dialog.m_add_button.isEnabled()
    assert not dialog.m_edit_action.isEnabled()
    assert not dialog.m_delete_action.isEnabled()
    assert dialog.m_table.rowCount() == 1
    updated = make_transaction(account_id, AccountTransactionType.DEPOSIT, "200")
    updated.transaction_id = transaction_id
    with pytest.raises(ValueError):
        journal.m_service.update_account_transaction(updated)
    with pytest.raises(ValueError):
        journal.m_service.delete_account_transaction(transaction_id)


def test_accounts_page_opens_details_on_double_click(qtbot, tmp_path, monkeypatch):
    """Verify the account identity flows to AccountDetailsDialog."""
    with JournalContext(tmp_path / "journal.db") as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))
        page = AccountsPage(journal.m_repository, journal.m_service)
        qtbot.addWidget(page)
        observed = []

        def accept_details(dialog):
            observed.append(dialog.m_account_id)
            return QDialog.Accepted

        monkeypatch.setattr(AccountDetailsDialog, "exec", accept_details)
        page.m_table.selectRow(0)
        page._open_account_details()
        assert observed == [account_id]
        assert page.m_table.item(0, 0).data(Qt.UserRole) == account_id
