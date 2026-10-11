# =============================================================================
# File: portfolio_metrics.py
# Purpose: Represent aggregated financial metrics across trading accounts.
# =============================================================================

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PortfolioMetrics:
    """
    Represent combined financial metrics across trading accounts.

    All monetary values are expressed as Decimal amounts.
    Market valuations and unrealized gains are not included.

    Attributes:
        account_count:
            Number of trading accounts included in the portfolio.
        total_deposits:
            Combined deposits recorded across accounts.
        total_withdrawals:
            Combined withdrawals recorded across accounts.
        net_contributions:
            Combined deposits minus withdrawals.
        cash_balance:
            Combined cash balance across accounts.
        realized_trading_pnl:
            Combined realized trading profit or loss.
        account_fees:
            Combined account-level fees.
        net_realized_pnl:
            Combined realized trading P&L minus account fees.
        open_position_cost_basis:
            Combined remaining cost basis of open positions.
        equity_at_cost_basis:
            Combined cash and open position cost basis.
    """

    account_count: int
    total_deposits: Decimal
    total_withdrawals: Decimal
    net_contributions: Decimal
    cash_balance: Decimal
    realized_trading_pnl: Decimal
    account_fees: Decimal
    net_realized_pnl: Decimal
    open_position_cost_basis: Decimal
    equity_at_cost_basis: Decimal
