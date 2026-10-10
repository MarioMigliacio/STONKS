# =============================================================================
# File: account_transaction.py
# Purpose: Defines non-trade account cash transactions.
# =============================================================================

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from stonks.journal.account_transaction_type import (
    AccountTransactionType,
)


@dataclass
class AccountTransaction:
    """
    Represents a non-trade cash movement in a trading account.

    Transactions record deposits, withdrawals, account-level
    fees, and adjustments independently of trade executions.

    Attributes:
        transaction_type:
            Category of account cash movement.

        occurred_at:
            Timestamp when the transaction occurred.

        amount:
            Positive monetary magnitude for the transaction,
            except adjustments, which may be signed.

        transaction_id:
            Unique database identifier. None before persistence.

        account_id:
            Identifier of the trading account associated with
            the cash transaction. None until ownership is assigned.

        notes:
            Additional information about the transaction.
    """

    transaction_type: AccountTransactionType
    occurred_at: datetime
    amount: Decimal

    transaction_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: str = ""

    @property
    def net_cash_flow(self) -> Decimal:
        """
        Calculate the signed account cash movement.

        Deposits increase cash, while withdrawals and fees
        decrease cash. Adjustments retain their signed amount.

        Returns:
            Decimal:
                Signed cash movement for the transaction.
        """
        if self.transaction_type == AccountTransactionType.DEPOSIT:
            return self.amount

        if self.transaction_type in (
            AccountTransactionType.WITHDRAWAL,
            AccountTransactionType.FEE,
        ):
            return -self.amount

        if self.transaction_type == AccountTransactionType.ADJUSTMENT:
            return self.amount

        raise ValueError(f"Unsupported transaction type: {self.transaction_type}")
