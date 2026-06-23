# =============================================================================
# File: account_snapshot.py
# Purpose: Defines account-level performance snapshots used by the
#          STONKS journal subsystem.
#
# Notes:
# - Account snapshots represent portfolio/account state at a point in time.
# - Used for tracking account growth, daily performance, and equity curves.
# - Separate from TradeOrder because account performance spans multiple
#   positions and trading days.
# =============================================================================

from dataclasses import dataclass

@dataclass
class AccountSnapshot:
    """
    Represents an account value snapshot.

    Attributes:
        snapshot_date:
            Date of the snapshot.

        account_value_before:
            Account value before trading activity.

        account_value_after:
            Account value after trading activity.

        notes:
            Optional notes about the trading session.
    """

    snapshot_date: str
    account_value_before: float
    account_value_after: float
    notes: str = ""

    @property
    def dollar_change(self) -> float:
        """Calculate account value change in dollars."""
        return self.account_value_after - self.account_value_before

    @property
    def percent_change(self) -> float:
        """Calculate account value change as a percentage."""
        if self.account_value_before == 0:
            return 0.0

        return (
            (self.account_value_after - self.account_value_before)
            / self.account_value_before
        ) * 100.0