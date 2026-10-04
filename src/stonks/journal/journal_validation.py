# =============================================================================
# File: journal_validation.py
# Purpose: Validates journal financial and timestamp data.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import (
    AccountTransactionType,
)
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.trade_execution import TradeExecution


def validate_timestamp(value: datetime) -> None:
    """
    Verify that a timestamp is timezone-aware.

    Args:
        value:
            Timestamp to validate.

    Raises:
        ValueError:
            If the timestamp has no valid timezone.
    """
    if not isinstance(value, datetime):
        raise ValueError("Timestamp must be a datetime.")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Journal timestamps must be timezone-aware.")


def normalize_timestamp(value: datetime) -> datetime:
    """
    Convert a timestamp to UTC.

    Args:
        value:
            Timezone-aware timestamp.

    Returns:
        datetime:
            Equivalent timestamp expressed in UTC.
    """
    validate_timestamp(value)

    return value.astimezone(timezone.utc)


def validate_decimal(
    value: Decimal,
    allow_negative: bool = False,
    allow_zero: bool = True,
) -> None:
    """
    Validate a financial decimal value.

    Args:
        value:
            Decimal amount to validate.

        allow_negative:
            Whether negative amounts are permitted.

        allow_zero:
            Whether zero is permitted.

    Raises:
        ValueError:
            If the value is invalid.
    """
    if not isinstance(value, Decimal):
        raise ValueError("Financial values must use Decimal.")

    if not value.is_finite():
        raise ValueError("Financial values must be finite.")

    if not allow_negative and value < 0:
        raise ValueError("Negative financial values are not permitted.")

    if not allow_zero and value == 0:
        raise ValueError("Zero is not permitted.")


def validate_execution(
    execution: TradeExecution,
) -> None:
    """
    Validate a trade execution's basic financial fields.

    Position balance and execution ordering are validated
    separately at the service level.

    Args:
        execution:
            Execution to validate.
    """
    if not isinstance(execution.side, ExecutionSide):
        raise ValueError("Invalid execution direction.")

    validate_decimal(
        execution.shares,
        allow_zero=False,
    )

    validate_decimal(
        execution.price,
        allow_zero=False,
    )

    validate_decimal(execution.fees)

    validate_timestamp(execution.executed_at)


def validate_account_transaction(
    transaction: AccountTransaction,
) -> None:
    """
    Validate an account transaction's financial fields.

    Args:
        transaction:
            Transaction to validate.
    """
    if not isinstance(
        transaction.transaction_type,
        AccountTransactionType,
    ):
        raise ValueError("Invalid account transaction type.")

    allow_negative = transaction.transaction_type == AccountTransactionType.ADJUSTMENT

    validate_decimal(
        transaction.amount,
        allow_negative=allow_negative,
        allow_zero=allow_negative,
    )

    validate_timestamp(transaction.occurred_at)
