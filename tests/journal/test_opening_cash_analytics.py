# =============================================================================
# File: test_opening_cash_analytics.py
# Purpose: Pytest file for test_opening_cash_analytics.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from stonks.journal.analytics.account_analytics import calculate_account_metrics
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def transaction(kind, amount, when):
    """Build a ledger transaction with a deterministic timestamp."""
    return AccountTransaction(kind, when, Decimal(amount))


def snapshot(amount="1000"):
    """Build the opening cash value at the known ledger boundary."""
    return OpeningCashBalance(1, Decimal(amount), START)


def test_snapshot_does_not_double_count_prior_deposit():
    """Cash starts at the snapshot, ignoring earlier cash movements."""
    transactions = [
        transaction(AccountTransactionType.DEPOSIT, "700", START - timedelta(days=1)),
        transaction(AccountTransactionType.WITHDRAWAL, "100", START + timedelta(days=1)),
    ]
    metrics = calculate_account_metrics(transactions, [], [], snapshot())
    assert metrics.cash_balance == Decimal("900")
    assert metrics.total_deposits == Decimal("700")
    assert metrics.total_withdrawals == Decimal("100")
    assert metrics.net_contributions == Decimal("600")
    assert metrics.net_realized_pnl == Decimal("0")
    assert metrics.equity_at_cost_basis == Decimal("900")


def test_boundary_includes_movements_at_exact_timestamp():
    """Cash events on the snapshot boundary are part of the new ledger."""
    metrics = calculate_account_metrics([transaction(AccountTransactionType.DEPOSIT, "25", START)], [], [], snapshot())
    assert metrics.cash_balance == Decimal("1025")


def test_snapshot_uses_aware_datetime_comparisons():
    """Offsets representing the same instant have the same boundary behavior."""
    equivalent_time = START.astimezone(timezone(timedelta(hours=-7)))
    metrics = calculate_account_metrics(
        [transaction(AccountTransactionType.WITHDRAWAL, "20", equivalent_time)], [], [], snapshot()
    )
    assert metrics.cash_balance == Decimal("980")


def test_trade_cash_history_respects_snapshot_boundary():
    """Earlier trade cash is not subtracted again from opening cash."""
    executions = [
        SimpleNamespace(executed_at=START - timedelta(days=1), net_cash_flow=Decimal("-400")),
        SimpleNamespace(executed_at=START + timedelta(days=1), net_cash_flow=Decimal("-125")),
    ]
    metrics = calculate_account_metrics([], executions, [], snapshot())
    assert metrics.cash_balance == Decimal("875")


def test_transfer_reallocates_cash_not_contributions():
    """Transfers change account cash without changing external contributions."""
    outgoing = transaction(AccountTransactionType.TRANSFER_OUT, "250", START + timedelta(days=1))
    incoming = transaction(AccountTransactionType.TRANSFER_IN, "250", START + timedelta(days=1))
    source = calculate_account_metrics([outgoing], [], [], snapshot("1000"))
    destination = calculate_account_metrics([incoming], [], [], snapshot("500"))
    assert source.cash_balance == Decimal("750")
    assert destination.cash_balance == Decimal("750")
    assert source.cash_balance + destination.cash_balance == Decimal("1500")
    assert source.net_contributions == destination.net_contributions == Decimal("0")
    assert source.net_realized_pnl == destination.net_realized_pnl == Decimal("0")


def test_missing_snapshot_preserves_legacy_calculation():
    """Existing analytics callers without snapshots retain original behavior."""
    movements = [
        transaction(AccountTransactionType.DEPOSIT, "700", START - timedelta(days=1)),
        transaction(AccountTransactionType.FEE, "10", START + timedelta(days=1)),
    ]
    metrics = calculate_account_metrics(movements, [], [])
    assert metrics.cash_balance == Decimal("690")
    assert metrics.net_contributions == Decimal("700")
    assert metrics.net_realized_pnl == Decimal("-10")


def test_snapshot_does_not_change_realized_pnl_or_fees():
    """Financial profitability is independent from opening cash."""
    transactions = [transaction(AccountTransactionType.FEE, "4", START + timedelta(days=1))]
    position = SimpleNamespace(realized_pnl=Decimal("80"), remaining_cost_basis=Decimal("30"))
    metrics = calculate_account_metrics(transactions, [], [position], snapshot("120"))
    assert metrics.cash_balance == Decimal("116")
    assert metrics.realized_trading_pnl == Decimal("80")
    assert metrics.account_fees == Decimal("4")
    assert metrics.net_realized_pnl == Decimal("76")
    assert metrics.open_position_cost_basis == Decimal("30")
    assert metrics.equity_at_cost_basis == Decimal("146")
