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
            External funds deposited into the trading account.

        WITHDRAWAL:
            External funds withdrawn from the trading account.

        FEE:
            Account-level expenses unrelated to executions.

        ADJUSTMENT:
            Other account cash adjustments.

        TRANSFER_IN:
            Funds received from another tracked trading account.

        TRANSFER_OUT:
            Funds sent to another tracked trading account.

    """

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    FEE = "FEE"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
