# =============================================================================
# File: portfolio_analytics.py
# Purpose: Calculate combined financial metrics across trading accounts.
# =============================================================================

from decimal import Decimal
from typing import List

from stonks.journal.analytics.account_metrics import AccountMetrics
from stonks.journal.analytics.portfolio_metrics import PortfolioMetrics


def calculate_portfolio_metrics(
    accounts: List[AccountMetrics],
) -> PortfolioMetrics:
    """
    Aggregate financial metrics across multiple trading accounts.

    This calculation sums the supplied account-level metrics without
    calculating market valuations. Internal transfers are already
    represented as offsetting cash movements across accounts.

    Args:
        accounts:
            Account-level financial metrics to aggregate.

    Returns:
        PortfolioMetrics:
            Combined financial metrics for the supplied accounts.
    """
    fields = (
        "total_deposits",
        "total_withdrawals",
        "net_contributions",
        "cash_balance",
        "realized_trading_pnl",
        "account_fees",
        "net_realized_pnl",
        "open_position_cost_basis",
        "equity_at_cost_basis",
    )

    totals = {
        field: sum(
            (getattr(account, field) for account in accounts),
            Decimal("0"),
        )
        for field in fields
    }

    return PortfolioMetrics(
        account_count=len(accounts),
        **totals,
    )
