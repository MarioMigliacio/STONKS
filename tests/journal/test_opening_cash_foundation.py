"""Tests for the D3.5A opening cash storage foundation."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository


@pytest.fixture
def account(tmp_path):
    """Create an isolated journal with one active account."""
    with JournalContext(tmp_path / "opening_cash.db") as context:
        account_id = context.m_service.create_trading_account(TradingAccount("Primary Cash", AccountType.CASH))
        yield context, account_id


def test_snapshot_is_separate_from_transaction_ledger(account):
    """Saving opening cash must not create a deposit or transaction."""
    context, account_id = account
    repository = OpeningCashRepository(context.m_connection)
    opening = OpeningCashBalance(
        account_id=account_id,
        amount=Decimal("1250.75"),
        effective_at=datetime(2026, 10, 1, 9, tzinfo=timezone(timedelta(hours=-7))),
    )
    with context.m_connection:
        repository.upsert(opening)

    saved = repository.get(account_id)
    assert saved.amount == Decimal("1250.75")
    assert saved.effective_at == datetime(2026, 10, 1, 16, tzinfo=timezone.utc)
    assert context.m_repository.get_account_transactions(account_id) == []


def test_update_retains_one_snapshot_per_account(account):
    """Updating a baseline replaces it rather than adding contributions."""
    context, account_id = account
    repository = OpeningCashRepository(context.m_connection)
    when = datetime(2026, 10, 1, tzinfo=timezone.utc)
    with context.m_connection:
        repository.upsert(OpeningCashBalance(account_id, Decimal("100"), when))
        repository.upsert(OpeningCashBalance(account_id, Decimal("300"), when))
    assert repository.get(account_id).amount == Decimal("300")
    count = context.m_connection.execute("SELECT COUNT(*) FROM account_opening_cash").fetchone()[0]
    assert count == 1


@pytest.mark.parametrize("amount", [Decimal("-1"), Decimal("NaN"), Decimal("Infinity"), 1.0])
def test_invalid_amount_is_rejected(account, amount):
    """Reject negative, non-finite, or float input."""
    context, account_id = account
    repo = OpeningCashRepository(context.m_connection)
    with pytest.raises(ValueError):
        repo.upsert(OpeningCashBalance(account_id, amount, datetime.now(timezone.utc)))
    assert repo.get(account_id) is None


def test_archived_account_cannot_change_snapshot(account):
    """Preserve archived account history while disallowing edits."""
    context, account_id = account
    other = context.m_service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))
    context.m_service.set_default_trading_account(other)
    context.m_service.archive_trading_account(account_id)
    repo = OpeningCashRepository(context.m_connection)
    with pytest.raises(ValueError, match="archived"):
        repo.upsert(OpeningCashBalance(account_id, Decimal("50"), datetime.now(timezone.utc)))


def test_missing_snapshot_is_not_implicitly_zero(account):
    """No baseline means unknown, not a verified zero-dollar cash balance."""
    context, account_id = account
    repo = OpeningCashRepository(context.m_connection)
    assert repo.get(account_id) is None
