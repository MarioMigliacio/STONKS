# =============================================================================
# File: test_cash_history_validation.py
# Purpose: Pytest file for test_cash_history_validation.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount
from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository
from stonks.journal.validation.cash_history_validation import validate_projected_cash_history

START = datetime(2026, 10, 1, tzinfo=timezone.utc)


@pytest.fixture
def journal(tmp_path):
    with JournalContext(tmp_path / "cash_validation.db") as context:
        source = context.m_service.create_trading_account(TradingAccount("Cash", AccountType.CASH))
        destination = context.m_service.create_trading_account(TradingAccount("IRA", AccountType.ROTH_IRA))
        opening = OpeningCashRepository(context.m_connection)
        with context.m_connection:
            opening.upsert(OpeningCashBalance(source, Decimal("1000"), START))
            opening.upsert(OpeningCashBalance(destination, Decimal("0"), START))
        yield context, source, destination


def check(context, accounts, additions=(), excluded=()):
    return validate_projected_cash_history(context.m_repository, context.m_connection, accounts, additions, excluded)


def test_valid_transfer_is_cash_neutral(journal):
    context, source, dest = journal
    check(context, (source, dest), ((source, START, Decimal("-250")), (dest, START, Decimal("250"))))


def test_rejects_amount_exceeding_opening_cash(journal):
    context, source, dest = journal
    with pytest.raises(ValueError, match="Insufficient"):
        check(context, (source, dest), ((source, START, Decimal("-1000.01")), (dest, START, Decimal("1000.01"))))


def test_later_cash_spend_invalidates_historical_edit(journal):
    context, source, dest = journal
    context.m_service.create_account_transaction(
        AccountTransaction(
            AccountTransactionType.WITHDRAWAL,
            START + timedelta(days=5),
            Decimal("700"),
            account_id=source,
        )
    )
    with pytest.raises(ValueError, match="Insufficient"):
        check(
            context,
            (source, dest),
            ((source, START + timedelta(days=1), Decimal("-400")), (dest, START + timedelta(days=1), Decimal("400"))),
        )


def test_edit_excludes_existing_transfer_to_avoid_double_count(journal):
    context, source, dest = journal
    out_id, in_id = context.m_service.create_account_transfer(source, dest, Decimal("600"), START + timedelta(days=1))
    check(
        context,
        (source, dest),
        ((source, START + timedelta(days=2), Decimal("-800")), (dest, START + timedelta(days=2), Decimal("800"))),
        (out_id, in_id),
    )
    with pytest.raises(ValueError, match="Insufficient"):
        check(
            context,
            (source, dest),
            ((source, START + timedelta(days=2), Decimal("-1001")), (dest, START + timedelta(days=2), Decimal("1001"))),
            (out_id, in_id),
        )


def test_rejects_event_before_snapshot(journal):
    context, source, dest = journal
    with pytest.raises(ValueError, match="precede"):
        check(context, (source, dest), ((source, START - timedelta(seconds=1), Decimal("-1")),))


def test_missing_snapshot_is_unknown_not_zero(journal):
    context, source, dest = journal
    third = context.m_service.create_trading_account(TradingAccount("Other", AccountType.CASH))
    with pytest.raises(ValueError, match="opening cash"):
        check(context, (source, third), ((source, START, Decimal("-1")), (third, START, Decimal("1"))))


def test_same_timestamp_netting_is_order_independent(journal):
    context, source, dest = journal
    instant = START + timedelta(days=1)
    check(
        context,
        (source, dest),
        ((source, instant, Decimal("-1300")), (source, instant, Decimal("300")), (dest, instant, Decimal("1000"))),
    )


def test_timezone_offsets_compare_same_instant(journal):
    context, source, dest = journal
    offset = timezone(timedelta(hours=-7))
    instant = START.astimezone(offset)
    check(context, (source, dest), ((source, instant, Decimal("-75")), (dest, START, Decimal("75"))))
