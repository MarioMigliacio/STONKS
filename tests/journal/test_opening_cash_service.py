# =============================================================================
# File: test_opening_cash_service.py
# Purpose: Check opening cash changes cannot invalidate paired transfers.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    """Make a small pair of tracked accounts with funded opening balances."""
    with JournalContext(tmp_path / "d35d.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        target = context.m_service.create_trading_account(TradingAccount("Roth", AccountType.ROTH_IRA))
        context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("100"), START))
        context.m_service.set_opening_cash(OpeningCashBalance(target, Decimal("0"), START))
        yield context, source, target


def test_save_opening_cash_without_creating_contribution(journal):
    """Saving an opening snapshot must not generate ledger transactions."""
    context, source, _ = journal
    assert OpeningCashRepository(context.m_connection).get(source).amount == Decimal("100")
    assert context.m_repository.get_account_transactions(source) == []


def test_reject_reduction_that_overdraws_prior_transfer(journal):
    """Lowering a baseline below existing cash outflows rolls back the change."""
    context, source, target = journal
    when = START + timedelta(days=1)
    context.m_service.create_account_transfer(source, target, Decimal("80"), when)
    with pytest.raises(ValueError, match="Insufficient"):
        context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("50"), START))
    assert OpeningCashRepository(context.m_connection).get(source).amount == Decimal("100")
    assert not context.m_connection.in_transaction


def test_reject_new_start_after_transfer(journal):
    """Moving the snapshot boundary past a recorded transfer is prohibited."""
    context, source, target = journal
    context.m_service.create_account_transfer(source, target, Decimal("10"), START + timedelta(days=1))
    with pytest.raises(ValueError, match="after an existing transfer"):
        context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("100"), START + timedelta(days=2)))
    assert OpeningCashRepository(context.m_connection).get(source).effective_at == START


def test_allow_safe_opening_balance_adjustment(journal):
    """Increasing the original cash amount preserves recorded transfer history."""
    context, source, target = journal
    context.m_service.create_account_transfer(source, target, Decimal("80"), START + timedelta(hours=1))
    context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("125"), START))
    assert OpeningCashRepository(context.m_connection).get(source).amount == Decimal("125")


def test_archived_account_cannot_edit_opening_cash(journal):
    """Archive rules apply to the service as well as the GUI."""
    context, source, target = journal
    context.m_service.set_default_trading_account(target)
    assert context.m_service.archive_trading_account(source)
    with pytest.raises(ValueError, match="archived"):
        context.m_service.set_opening_cash(OpeningCashBalance(source, Decimal("300"), START))
