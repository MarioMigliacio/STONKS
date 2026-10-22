# =============================================================================
# File: test_journal_analyzer_opening_cash.py
# Purpose: Verify analyzer cash metrics honor persisted opening snapshots.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from stonks.journal.analytics.journal_analyzer import analyze_account, analyze_portfolio
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_transaction import AccountTransaction
from stonks.journal.models.account_transaction_type import AccountTransactionType
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.opening_cash_balance import OpeningCashBalance
from stonks.journal.models.trading_account import TradingAccount

START = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def _account(context, name: str, opening=None) -> int:
    """Create a tracked cash account with an optional dated opening snapshot.

    Args:
        context:
            Open journal context providing persistence and validated services.
        name:
            Display name for the new account.
        opening:
            Optional starting cash value represented as a Decimal.

    Returns:
        int:
            Database identifier of the created account.
    """
    account_id = context.m_service.create_trading_account(TradingAccount(name, AccountType.CASH))

    if opening is not None:
        context.m_service.set_opening_cash(OpeningCashBalance(account_id, Decimal(opening), START))

    return account_id


def _post(context, account_id: int, kind: AccountTransactionType, amount: str, when: datetime) -> int:
    """Persist a cash movement through the validated journal service.

    Args:
        context:
            Open journal context.
        account_id:
            Owner of the transaction.
        kind:
            Cash transaction type.
        amount:
            Monetary magnitude encoded as a Decimal-compatible string.
        when:
            Timezone-aware timestamp of the movement.

    Returns:
        int:
            Database identifier of the persisted transaction.
    """
    return context.m_service.create_account_transaction(
        AccountTransaction(
            transaction_type=kind,
            occurred_at=when,
            amount=Decimal(amount),
            account_id=account_id,
        )
    )


def test_analyze_account_uses_saved_opening_cash_and_boundary(tmp_path):
    """Avoid double-counting historical deposits already in the snapshot."""
    with JournalContext(tmp_path / "analyzer_boundary.db") as journal:
        account_id = _account(journal, "Roth")
        _post(journal, account_id, AccountTransactionType.DEPOSIT, "700", START - timedelta(days=1))
        journal.m_service.set_opening_cash(OpeningCashBalance(account_id, Decimal("1000"), START))
        _post(journal, account_id, AccountTransactionType.WITHDRAWAL, "100", START + timedelta(days=1))

        metrics = analyze_account(journal.m_repository, account_id)

        assert metrics.cash_balance == Decimal("900")
        assert metrics.equity_at_cost_basis == Decimal("900")
        # Contributions remain all-period historical measurements.
        assert metrics.total_deposits == Decimal("700")
        assert metrics.total_withdrawals == Decimal("100")
        assert metrics.net_contributions == Decimal("600")


def test_analyze_portfolio_aggregates_snapshot_aware_cash(tmp_path):
    """Portfolio metrics sum account cash without double-counting old deposits."""
    with JournalContext(tmp_path / "analyzer_portfolio.db") as journal:
        first = _account(journal, "Primary", "1000")
        second = _account(journal, "Secondary", "200")
        _post(journal, first, AccountTransactionType.WITHDRAWAL, "100", START + timedelta(days=1))
        _post(journal, second, AccountTransactionType.DEPOSIT, "25", START + timedelta(days=1))

        primary = analyze_account(journal.m_repository, first)
        secondary = analyze_account(journal.m_repository, second)
        portfolio = analyze_portfolio(journal.m_repository, [first, second])

        assert primary.cash_balance == Decimal("900")
        assert secondary.cash_balance == Decimal("225")
        assert portfolio.cash_balance == Decimal("1125")
        assert portfolio.equity_at_cost_basis == Decimal("1125")
        assert portfolio.net_contributions == Decimal("-75")


def test_analyze_account_without_opening_preserves_legacy_cash(tmp_path):
    """Unverified accounts continue calculating cash from recorded movements."""
    with JournalContext(tmp_path / "analyzer_legacy.db") as journal:
        account_id = _account(journal, "Unverified")
        _post(journal, account_id, AccountTransactionType.DEPOSIT, "75", START)
        _post(journal, account_id, AccountTransactionType.FEE, "5", START + timedelta(days=1))

        metrics = analyze_account(journal.m_repository, account_id)

        assert metrics.cash_balance == Decimal("70")
        assert metrics.net_contributions == Decimal("75")
        assert metrics.net_realized_pnl == Decimal("-5")
