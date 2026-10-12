# =============================================================================
# File: test_portfolio_analytics.py
# Purpose: Verify portfolio-level financial metric aggregation.
# =============================================================================

from decimal import Decimal

import pytest

from stonks.journal.analytics.account_metrics import AccountMetrics
from stonks.journal.analytics.portfolio_analytics import calculate_portfolio_metrics


def create_test_account_metrics(
    deposits: str = "1000",
    withdrawals: str = "0",
    cash: str = "1000",
    trading_pnl: str = "0",
    fees: str = "0",
    cost_basis: str = "0",
) -> AccountMetrics:
    """
    Construct account metrics with internally consistent derived values.

    Args:
        deposits:
            Total recorded deposits.
        withdrawals:
            Total recorded withdrawals.
        cash:
            Remaining cash balance.
        trading_pnl:
            Realized trading profit or loss.
        fees:
            Account-level fees.
        cost_basis:
            Remaining open position cost basis.

    Returns:
        AccountMetrics:
            Representative account metrics for testing.
    """
    return AccountMetrics(
        total_deposits=Decimal(deposits),
        total_withdrawals=Decimal(withdrawals),
        net_contributions=Decimal(deposits) - Decimal(withdrawals),
        cash_balance=Decimal(cash),
        realized_trading_pnl=Decimal(trading_pnl),
        account_fees=Decimal(fees),
        net_realized_pnl=Decimal(trading_pnl) - Decimal(fees),
        open_position_cost_basis=Decimal(cost_basis),
        equity_at_cost_basis=Decimal(cash) + Decimal(cost_basis),
    )


@pytest.mark.parametrize(
    "accounts",
    [
        [],
        [
            create_test_account_metrics(
                deposits="1000",
                withdrawals="100",
                cash="500",
                trading_pnl="75",
                fees="5",
                cost_basis="400",
            )
        ],
        [
            create_test_account_metrics(
                deposits="2000",
                withdrawals="200",
                cash="1200",
                trading_pnl="150",
                fees="10",
                cost_basis="800",
            ),
            create_test_account_metrics(
                deposits="1500",
                withdrawals="100",
                cash="900",
                trading_pnl="-50",
                fees="5",
                cost_basis="600",
            ),
        ],
    ],
)
def test_portfolio_financial_invariants(accounts) -> None:
    """Verify aggregated portfolio metrics preserve accounting identities."""
    metrics = calculate_portfolio_metrics(accounts)

    assert metrics.net_contributions == (metrics.total_deposits - metrics.total_withdrawals)

    assert metrics.net_realized_pnl == (metrics.realized_trading_pnl - metrics.account_fees)

    assert metrics.equity_at_cost_basis == (metrics.cash_balance + metrics.open_position_cost_basis)


def test_empty_portfolio() -> None:
    """Verify an empty portfolio produces zero-valued metrics."""
    result = calculate_portfolio_metrics([])

    assert result.account_count == 0

    for field in (
        "total_deposits",
        "total_withdrawals",
        "net_contributions",
        "cash_balance",
        "realized_trading_pnl",
        "account_fees",
        "net_realized_pnl",
        "open_position_cost_basis",
        "equity_at_cost_basis",
    ):
        assert getattr(result, field) == Decimal("0")
        assert isinstance(getattr(result, field), Decimal)


def test_single_account_portfolio() -> None:
    """Verify a single account retains its original financial values."""
    account = create_test_account_metrics(
        deposits="2500",
        withdrawals="200",
        cash="1300",
        trading_pnl="150",
        fees="5",
        cost_basis="1000",
    )

    result = calculate_portfolio_metrics([account])

    assert result.account_count == 1
    assert result.total_deposits == account.total_deposits
    assert result.total_withdrawals == account.total_withdrawals
    assert result.net_contributions == account.net_contributions
    assert result.cash_balance == account.cash_balance
    assert result.realized_trading_pnl == account.realized_trading_pnl
    assert result.account_fees == account.account_fees
    assert result.net_realized_pnl == account.net_realized_pnl
    assert result.open_position_cost_basis == account.open_position_cost_basis
    assert result.equity_at_cost_basis == account.equity_at_cost_basis


def test_multiple_account_portfolio() -> None:
    """Verify aggregation combines gains, losses, and account balances."""
    roth = create_test_account_metrics(
        deposits="2000",
        withdrawals="100",
        cash="1200",
        trading_pnl="250",
        fees="5",
        cost_basis="800",
    )

    cash_account = create_test_account_metrics(
        deposits="1500",
        withdrawals="50",
        cash="600",
        trading_pnl="-75",
        fees="3",
        cost_basis="900",
    )

    result = calculate_portfolio_metrics([roth, cash_account])

    assert result.account_count == 2
    assert result.total_deposits == Decimal("3500")
    assert result.total_withdrawals == Decimal("150")
    assert result.net_contributions == Decimal("3350")
    assert result.cash_balance == Decimal("1800")
    assert result.realized_trading_pnl == Decimal("175")
    assert result.account_fees == Decimal("8")
    assert result.net_realized_pnl == Decimal("167")
    assert result.open_position_cost_basis == Decimal("1700")
    assert result.equity_at_cost_basis == Decimal("3500")
