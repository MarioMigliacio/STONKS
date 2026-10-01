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
    Represents an account value snapshot for a trading session.

    Records account values before and after trading activity.
    Provides calculated dollar and percentage changes for
    tracking account performance over time.

    Changes in account value may include deposits, withdrawals,
    or other adjustments and do not necessarily represent
    realized trading profit or loss.

    Attributes:
        snapshot_date:
            Date associated with the account snapshot, stored
            as a string in the journal's existing date format.

        account_value_before:
            Total account value before the trading session,
            expressed in dollars.

        account_value_after:
            Total account value after the trading session,
            expressed in dollars.

        notes:
            Optional notes about the trading session.
            Defaults to an empty string.
    """

    snapshot_date: str
    account_value_before: float
    account_value_after: float
    notes: str = ""

    @property
    def dollar_change(self) -> float:
        """
        Calculate the change in account value.

        Returns:
            float:
                Difference between the account value after
                and before the trading session, in dollars.

                A positive value represents an increase;
                a negative value represents a decrease.
        """
        return self.account_value_after - self.account_value_before

    @property
    def percent_change(self) -> float:
        """
        Calculate the percentage change in account value.

        Returns:
            float:
                Percentage change relative to the account
                value before the trading session.

                Returns 0.0 if the starting account value
                is zero.

        Notes:
            This calculation does not account for deposits,
            withdrawals, or other external cash movements.
        """
        if self.account_value_before == 0:
            return 0.0

        return ((self.account_value_after - self.account_value_before) / self.account_value_before) * 100.0
