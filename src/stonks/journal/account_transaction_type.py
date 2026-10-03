# =============================================================================
# File: account_transaction_type.py
# Purpose: Defines supported journal account transaction types.
# =============================================================================

from enum import Enum


class AccountTransactionType(str, Enum):
    """
    Represents a non-trade account transaction.

    Values:
        DEPOSIT:
            Funds transferred into the trading account.

        WITHDRAWAL:
            Funds transferred out of the trading account.

        FEE:
            Account-level expenses unrelated to executions.

        ADJUSTMENT:
            Other account cash adjustments.
    """

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    FEE = "FEE"
    ADJUSTMENT = "ADJUSTMENT"
