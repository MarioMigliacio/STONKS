# =============================================================================
# File: test_journal_analyzer.py
# Purpose: Pytest file for test_journal_analyzer.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import AccountTransactionType
from stonks.journal.account_type import AccountType
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_analyzer import (
    analyze_account,
    analyze_portfolio,
)
from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.position import Position
from stonks.journal.trade_execution import TradeExecution
from stonks.journal.trading_account import TradingAccount


@pytest.fixture
def repository(tmp_path: Path):
    """
    Provide an initialized journal repository with one trading account.

    Args:
        tmp_path:
            Temporary directory provided by pytest.

    Yields:
        JournalRepository:
            Repository connected to an isolated SQLite test database.
    """
    database_path = tmp_path / "test_journal_analyzer.db"

    initialize_database(database_path)
    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)

        with connection:
            account_id = repository.create_trading_account(
                TradingAccount(
                    name="Test Roth IRA",
                    account_type=AccountType.ROTH_IRA,
                    broker="Webull",
                    is_default=True,
                )
            )

        repository.test_account_id = account_id

        yield repository

    finally:
        connection.close()


def test_analyze_empty_account(
    repository: JournalRepository,
) -> None:
    """Verify an empty account produces zero-valued financial metrics."""
    metrics = analyze_account(
        repository,
        repository.test_account_id,
    )

    assert metrics.total_deposits == Decimal("0")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("0")
    assert metrics.cash_balance == Decimal("0")
    assert metrics.realized_trading_pnl == Decimal("0")
    assert metrics.account_fees == Decimal("0")
    assert metrics.net_realized_pnl == Decimal("0")
    assert metrics.open_position_cost_basis == Decimal("0")
    assert metrics.equity_at_cost_basis == Decimal("0")


def test_analyze_unknown_account(
    repository: JournalRepository,
) -> None:
    """Verify analytics rejects nonexistent trading accounts."""
    with pytest.raises(
        ValueError,
        match="Trading account 999 does not exist",
    ):
        analyze_account(repository, account_id=999)


def test_analyze_account_with_draft_position(
    repository: JournalRepository,
) -> None:
    """Verify draft positions do not affect account financial metrics."""
    with repository.m_connection:
        repository.create_position(
            Position(
                account_id=repository.test_account_id,
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Awaiting breakout confirmation",
            )
        )

    metrics = analyze_account(
        repository,
        repository.test_account_id,
    )

    assert metrics.cash_balance == Decimal("0")
    assert metrics.realized_trading_pnl == Decimal("0")
    assert metrics.open_position_cost_basis == Decimal("0")
    assert metrics.equity_at_cost_basis == Decimal("0")


def test_analyze_account_with_partial_sale(
    repository: JournalRepository,
) -> None:
    """
    Verify account analytics combine cash flows, partial exits,
    execution fees, and account-level expenses.
    """
    account_id = repository.test_account_id

    with repository.m_connection:
        repository.create_account_transaction(
            AccountTransaction(
                account_id=account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("1000"),
            )
        )

        position_id = repository.create_position(
            Position(
                account_id=account_id,
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Breakout confirmation",
            )
        )

        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(2026, 9, 30, 13, 30, tzinfo=timezone.utc),
                shares=Decimal("10"),
                price=Decimal("50"),
                fees=Decimal("1"),
            )
        )

        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.SELL,
                executed_at=datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc),
                shares=Decimal("4"),
                price=Decimal("60"),
                fees=Decimal("1"),
            )
        )

        repository.create_account_transaction(
            AccountTransaction(
                account_id=account_id,
                transaction_type=AccountTransactionType.FEE,
                occurred_at=datetime(2026, 9, 30, 14, 30, tzinfo=timezone.utc),
                amount=Decimal("2"),
            )
        )

    metrics = analyze_account(repository, account_id)

    assert metrics.total_deposits == Decimal("1000")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("1000")

    assert metrics.cash_balance == Decimal("736")
    assert metrics.realized_trading_pnl == Decimal("38.60")
    assert metrics.account_fees == Decimal("2")
    assert metrics.net_realized_pnl == Decimal("36.60")

    assert metrics.open_position_cost_basis == Decimal("300.60")
    assert metrics.equity_at_cost_basis == Decimal("1036.60")


def test_analyze_account_isolation(
    repository: JournalRepository,
) -> None:
    """Verify financial activity remains isolated by trading account."""
    first_account_id = repository.test_account_id

    with repository.m_connection:
        second_account_id = repository.create_trading_account(
            TradingAccount(
                name="Test Cash Account",
                account_type=AccountType.CASH,
                broker="Webull",
                is_default=False,
            )
        )

        repository.create_account_transaction(
            AccountTransaction(
                account_id=first_account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("1000"),
            )
        )

        repository.create_account_transaction(
            AccountTransaction(
                account_id=second_account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("2500"),
            )
        )

        position_id = repository.create_position(
            Position(
                account_id=second_account_id,
                ticker="AMD",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Breakout confirmation",
            )
        )

        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(2026, 9, 30, 13, 30, tzinfo=timezone.utc),
                shares=Decimal("10"),
                price=Decimal("50"),
                fees=Decimal("1"),
            )
        )

    first_metrics = analyze_account(repository, first_account_id)
    second_metrics = analyze_account(repository, second_account_id)

    assert first_metrics.total_deposits == Decimal("1000")
    assert first_metrics.cash_balance == Decimal("1000")
    assert first_metrics.open_position_cost_basis == Decimal("0")

    assert second_metrics.total_deposits == Decimal("2500")
    assert second_metrics.cash_balance == Decimal("1999")
    assert second_metrics.open_position_cost_basis == Decimal("501")
    assert second_metrics.equity_at_cost_basis == Decimal("2500")


def test_analyze_archived_account(
    repository: JournalRepository,
) -> None:
    """Verify archived trading accounts remain eligible for analysis."""
    with repository.m_connection:
        archived_account_id = repository.create_trading_account(
            TradingAccount(
                name="Archived Cash Account",
                account_type=AccountType.CASH,
                broker="Webull",
                is_default=False,
            )
        )

        repository.create_account_transaction(
            AccountTransaction(
                account_id=archived_account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("1500"),
            )
        )

        account = repository.get_trading_account(archived_account_id)
        assert account is not None

        account.is_active = False
        repository.update_trading_account(account)

    metrics = analyze_account(repository, archived_account_id)

    assert metrics.total_deposits == Decimal("1500")
    assert metrics.cash_balance == Decimal("1500")
    assert metrics.net_contributions == Decimal("1500")


def test_analyze_empty_portfolio_selection(
    repository: JournalRepository,
) -> None:
    """Verify an explicit empty selection produces zero-valued metrics."""
    metrics = analyze_portfolio(repository, account_ids=[])

    assert metrics.account_count == 0
    assert metrics.total_deposits == Decimal("0")
    assert metrics.cash_balance == Decimal("0")
    assert metrics.net_realized_pnl == Decimal("0")
    assert metrics.equity_at_cost_basis == Decimal("0")


def test_analyze_portfolio_unknown_account(
    repository: JournalRepository,
) -> None:
    """Verify portfolio analytics rejects nonexistent account IDs."""
    with pytest.raises(
        ValueError,
        match="Trading account 999 does not exist",
    ):
        analyze_portfolio(repository, account_ids=[999])


def test_analyze_portfolio_deduplicates_accounts(
    repository: JournalRepository,
) -> None:
    """Verify duplicate account IDs do not inflate portfolio metrics."""
    account_id = repository.test_account_id

    with repository.m_connection:
        repository.create_account_transaction(
            AccountTransaction(
                account_id=account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("1000"),
            )
        )

    metrics = analyze_portfolio(
        repository,
        account_ids=[account_id, account_id],
    )

    assert metrics.account_count == 1
    assert metrics.total_deposits == Decimal("1000")
    assert metrics.cash_balance == Decimal("1000")


def test_analyze_portfolio_multiple_accounts(
    repository: JournalRepository,
) -> None:
    """
    Verify portfolio analytics combine multiple accounts,
    including archived accounts and realized trading gains.
    """
    first_account_id = repository.test_account_id

    with repository.m_connection:
        second_account_id = repository.create_trading_account(
            TradingAccount(
                name="Test Cash Account",
                account_type=AccountType.CASH,
                broker="Webull",
                is_default=False,
            )
        )

        # Account 1: Deposit $1,000.
        repository.create_account_transaction(
            AccountTransaction(
                account_id=first_account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("1000"),
            )
        )

        # Account 2: Deposit $2,000.
        repository.create_account_transaction(
            AccountTransaction(
                account_id=second_account_id,
                transaction_type=AccountTransactionType.DEPOSIT,
                occurred_at=datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
                amount=Decimal("2000"),
            )
        )

        position_id = repository.create_position(
            Position(
                account_id=second_account_id,
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
                entry_reason="Breakout confirmation",
            )
        )

        # Buy 10 shares at $50 with a $1 fee.
        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(2026, 9, 30, 13, 30, tzinfo=timezone.utc),
                shares=Decimal("10"),
                price=Decimal("50"),
                fees=Decimal("1"),
            )
        )

        # Sell all 10 shares at $60 with a $1 fee.
        repository.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.SELL,
                executed_at=datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc),
                shares=Decimal("10"),
                price=Decimal("60"),
                fees=Decimal("1"),
            )
        )

        # Archive the second account after recording its history.
        account = repository.get_trading_account(second_account_id)
        assert account is not None

        account.is_active = False
        repository.update_trading_account(account)

    metrics = analyze_portfolio(repository)

    assert metrics.account_count == 2
    assert metrics.total_deposits == Decimal("3000")
    assert metrics.total_withdrawals == Decimal("0")
    assert metrics.net_contributions == Decimal("3000")

    # Account 1: $1,000
    # Account 2: $2,000 - $501 + $599 = $2,098
    assert metrics.cash_balance == Decimal("3098")

    # Realized trading profit: $600 - $1 - $500 - $1
    assert metrics.realized_trading_pnl == Decimal("98")
    assert metrics.account_fees == Decimal("0")
    assert metrics.net_realized_pnl == Decimal("98")

    # Position is fully closed.
    assert metrics.open_position_cost_basis == Decimal("0")
    assert metrics.equity_at_cost_basis == Decimal("3098")

    selected_metrics = analyze_portfolio(
        repository,
        account_ids=[first_account_id],
    )

    assert selected_metrics.account_count == 1
    assert selected_metrics.total_deposits == Decimal("1000")
    assert selected_metrics.cash_balance == Decimal("1000")
    assert selected_metrics.realized_trading_pnl == Decimal("0")
