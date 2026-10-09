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
            Calculated account cash balance after applying account
            transactions and trade execution cash flows.
    """

    total_deposits: Decimal
    total_withdrawals: Decimal
    net_contributions: Decimal
    cash_balance: Decimal
