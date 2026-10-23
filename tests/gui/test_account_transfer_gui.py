# =============================================================================
# File: test_account_transfer_gui.py
# Purpose: Pytest file for test_account_transfer_gui.py
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from stonks.gui.pages.account_details_dialog import AccountDetailsDialog
from stonks.gui.pages.account_transfer_dialog import AccountTransferDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository


@pytest.fixture
def transfer_gui(qtbot, tmp_path):
    """Provide an account detail dialog with two active tracked accounts."""
    with JournalContext(tmp_path / "transfer_gui.db") as journal:
        source = journal.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = journal.m_service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))

        opening_repo = OpeningCashRepository(journal.m_connection)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with journal.m_connection:
            opening_repo.upsert(OpeningCashBalance(source, Decimal("10000"), start))
            opening_repo.upsert(OpeningCashBalance(destination, Decimal("10000"), start))

        details = AccountDetailsDialog(source, journal.m_repository, journal.m_service)
        qtbot.addWidget(details)
        yield journal, source, destination, details


def _accept_new_transfer(form):
    """Simulate entering a valid transfer into the modal editor."""
    form.m_source.setCurrentIndex(form.m_source.findData(1))
    form.m_destination.setCurrentIndex(form.m_destination.findData(2))
    form.m_amount.setText("125.50")
    form.m_notes.setPlainText("Reallocation")
    return QDialog.Accepted


def test_transfer_button_creates_linked_records(transfer_gui, monkeypatch):
    """Creating a transfer writes two balanced legs visible in both accounts."""
    journal, source, destination, details = transfer_gui
    monkeypatch.setattr(AccountTransferDialog, "exec", _accept_new_transfer)
    assert details.m_transfer_button.isEnabled()
    details.m_transfer_button.click()
    outgoing = journal.m_repository.get_account_transactions(source)
    incoming = journal.m_repository.get_account_transactions(destination)
    assert len(outgoing) == len(incoming) == 1
    assert outgoing[0].transfer_id == incoming[0].transfer_id
    assert outgoing[0].amount == incoming[0].amount == Decimal("125.50")
    assert outgoing[0].net_cash_flow + incoming[0].net_cash_flow == 0
    assert details.m_table.rowCount() == 1


def test_transfer_row_edit_and_delete(transfer_gui, monkeypatch):
    """Transfer rows use paired service operations instead of ordinary CRUD."""
    journal, source, destination, details = transfer_gui
    monkeypatch.setattr(AccountTransferDialog, "exec", _accept_new_transfer)
    details.m_transfer_button.click()
    details.m_table.selectRow(0)
    assert details.m_edit_transfer_action.isEnabled()
    assert details.m_delete_transfer_action.isEnabled()
    assert not details.m_edit_action.isEnabled()
    assert not details.m_delete_action.isEnabled()

    def accept_edit(form):
        assert form.m_transfer is not None
        assert not form.m_source.isEnabled()
        assert not form.m_destination.isEnabled()
        form.m_amount.setText("200.25")
        return QDialog.Accepted

    monkeypatch.setattr(AccountTransferDialog, "exec", accept_edit)
    details.m_edit_transfer_action.trigger()
    assert journal.m_repository.get_account_transactions(source)[0].amount == Decimal("200.25")
    assert journal.m_repository.get_account_transactions(destination)[0].amount == Decimal("200.25")
    details.m_table.selectRow(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    details.m_delete_transfer_action.trigger()
    assert journal.m_repository.get_account_transactions(source) == []
    assert journal.m_repository.get_account_transactions(destination) == []
    assert details.m_table.rowCount() == 0


def test_archived_account_transfer_actions_are_disabled(transfer_gui):
    """Archived account details display transfers without exposing mutations."""
    journal, source, destination, details = transfer_gui
    from datetime import datetime, timezone

    journal.m_service.create_account_transfer(source, destination, Decimal("50"), datetime.now(timezone.utc))
    journal.m_service.set_default_trading_account(destination)
    journal.m_service.archive_trading_account(source)
    details.refresh_details()
    details.m_table.selectRow(0)
    assert not details.m_transfer_button.isEnabled()
    assert not details.m_edit_transfer_action.isEnabled()
    assert not details.m_delete_transfer_action.isEnabled()
