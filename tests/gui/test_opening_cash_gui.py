# =============================================================================
# File: test_opening_cash_gui.py
# Purpose: Validate opening cash controls and opening-aware account metrics.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.account_details_dialog import AccountDetailsDialog
from stonks.gui.pages.opening_cash_dialog import OpeningCashDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository


@pytest.fixture
def account(qtbot, tmp_path):
    """Provide a real Account Details dialog backed by temporary SQLite."""
    with JournalContext(tmp_path / "d35d_gui.db") as context:
        account_id = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        dialog = AccountDetailsDialog(account_id, context.m_repository, context.m_service)
        qtbot.addWidget(dialog)
        yield context, account_id, dialog


def test_missing_opening_cash_is_visible(account):
    """Do not imply that an absent opening snapshot is verified zero cash."""
    _, _, dialog = account
    assert "Not set" in dialog.m_opening_cash_label.text()
    assert dialog.m_opening_cash_button.isEnabled()


def test_opening_cash_button_saves_and_refreshes_metrics(account, monkeypatch):
    """The control saves a snapshot without creating a deposit."""
    context, account_id, dialog = account

    def accept_opening(form):
        form.m_amount.setText("1250.75")
        form.m_effective_at.setDateTime(datetime(2026, 10, 1, tzinfo=timezone.utc))
        return QDialog.Accepted

    monkeypatch.setattr(OpeningCashDialog, "exec", accept_opening)
    dialog.m_opening_cash_button.click()
    opening = OpeningCashRepository(context.m_connection).get(account_id)
    assert opening is not None
    assert opening.amount == Decimal("1250.75")
    assert context.m_repository.get_account_transactions(account_id) == []
    assert dialog.m_metrics.m_cash_balance.text() == "$1,250.75"
    assert dialog.m_metrics.m_contributions.text() == "$0.00"


def test_archived_account_cannot_edit_opening_cash(account):
    """The opening balance stays visible but the edit action becomes read-only."""
    context, account_id, dialog = account
    other = context.m_service.create_trading_account(TradingAccount("Roth", AccountType.ROTH_IRA))
    context.m_service.set_default_trading_account(other)
    context.m_service.archive_trading_account(account_id)
    dialog.refresh_details()
    assert not dialog.m_opening_cash_button.isEnabled()
