# =============================================================================
# File: account_metrics.py
# Purpose: Represents calculated account deposits and withdrawal metrics.
# =============================================================================

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AccountMetrics:
    """
    Represent calculated financial metrics for a trading account.

    Attributes:
        total_deposits:
            Total amount of money deposited into the account.

        total_withdrawals:
            Total amount of money withdrawn from the account.

        net_contributions:
            Net external capital contributed to the account,
            calculated as deposits minus withdrawals.

        cash_balance:
            Ledger-derived cash balance after applying account
            transactions and trade execution cash flows.

        realized_trading_pnl:
            Combined realized profit or loss across trading positions,
            including allocated purchase fees and selling fees.

        account_fees:
            Total standalone account-level fees, excluding fees
            already included in trade execution calculations.

        net_realized_pnl:
            Combined realized trading profit or loss after
            deducting standalone account-level fees.
            Excludes unrealized gains, losses, and cash adjustments.

        open_position_cost_basis:
            Combined remaining cost basis of all open trading
            positions, including allocated purchase fees.
            Excludes unrealized gains and losses.

        equity_at_cost_basis:
            Estimated account book value calculated as cash
            balance plus remaining open position cost basis.
            Does not represent current market-value equity.
    """

    total_deposits: Decimal
    total_withdrawals: Decimal
    net_contributions: Decimal
    cash_balance: Decimal
    realized_trading_pnl: Decimal
    account_fees: Decimal
    net_realized_pnl: Decimal
    open_position_cost_basis: Decimal
    equity_at_cost_basis: Decimal
