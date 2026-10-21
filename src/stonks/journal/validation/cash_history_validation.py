# =============================================================================
# File: cash_history_validation.py
# Purpose: Validate dated journal cash balances against opening snapshots.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Tuple

from stonks.journal.persistence.opening_cash_repository import OpeningCashRepository

# Account ID, timestamp, signed cash movement.
CashChange = Tuple[int, datetime, Decimal]


def _as_utc(value: datetime) -> datetime:
    """Normalize an aware timestamp so all cash events sort consistently."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Cash event timestamps must be timezone-aware.")
    return value.astimezone(timezone.utc)


def validate_projected_cash_history(
    repository,
    connection,
    account_ids: Iterable[int],
    additions: Iterable[CashChange] = (),
    excluded_transaction_ids: Iterable[int] = (),
) -> None:
    """Reject a proposed ledger change if it causes a negative recorded cash balance.

    Uses each account's dated opening cash snapshot as the first known balance.
    Transactions and executions before the snapshot are not counted. Cash
    movements at the same timestamp are combined before testing a balance;
    no arbitrary transaction ID order decides an overdraft.

    This is a pure read/validation operation. Callers making writes must run
    it INSIDE the same service transaction as the eventual changes.

    Args:
        repository:
            JournalRepository used to read account transactions and executions.
        connection:
            Shared SQLite connection containing opening snapshots.
        account_ids:
            Tracked account identifiers whose projected cash will be checked.
        additions:
            Replacement or proposed (account_id, timestamp, signed flow) events.
        excluded_transaction_ids:
            Persisted ledger transaction IDs to exclude (for transfer editing).

    Raises:
        ValueError:
            If a snapshot is missing, a proposed event predates its snapshot,
            or the projected balance becomes negative.
    """
    excluded = set(excluded_transaction_ids)
    proposed = [(account_id, _as_utc(when), flow) for account_id, when, flow in additions]
    opening_repository = OpeningCashRepository(connection)

    for account_id in set(account_ids):
        opening = opening_repository.get(account_id)
        if opening is None:
            raise ValueError(f"Account {account_id} needs an opening cash balance before transfers.")

        boundary = _as_utc(opening.effective_at)
        events = {}

        def apply(when: datetime, amount: Decimal) -> None:
            instant = _as_utc(when)
            if instant < boundary:
                return
            events[instant] = events.get(instant, Decimal("0")) + amount

        for transaction in repository.get_account_transactions(account_id):
            if transaction.transaction_id not in excluded:
                apply(transaction.occurred_at, transaction.net_cash_flow)

        for execution in repository.get_executions(account_id):
            apply(execution.executed_at, execution.net_cash_flow)

        for changed_account, when, flow in proposed:
            if changed_account == account_id:
                if when < boundary:
                    raise ValueError("Transfer date cannot precede the account opening cash snapshot.")
                if not isinstance(flow, Decimal) or not flow.is_finite():
                    raise ValueError("Projected cash movements must be finite Decimal amounts.")
                apply(when, flow)

        balance = opening.amount
        for instant in sorted(events):
            balance += events[instant]
            if balance < 0:
                raise ValueError(
                    f"Insufficient recorded cash in account {account_id} "
                    f"at {instant.isoformat()}: deficit {abs(balance)}."
                )
