# =============================================================================
# File: test_journal_validation.py
# Purpose: Pytest file for test_journal_validation.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.account_transaction import AccountTransaction
from stonks.journal.account_transaction_type import (
    AccountTransactionType,
)
from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_validation import (
    normalize_timestamp,
    validate_account_transaction,
    validate_decimal,
    validate_execution,
    validate_timestamp,
)
from stonks.journal.trade_execution import TradeExecution


def create_test_execution() -> TradeExecution:
    """Create a valid execution for validation tests."""

    return TradeExecution(
        position_id=1,
        side=ExecutionSide.BUY,
        executed_at=datetime(
            2026,
            9,
            30,
            13,
            30,
            tzinfo=timezone.utc,
        ),
        shares=Decimal("10"),
        price=Decimal("12.50"),
        fees=Decimal("0.00"),
    )


def test_valid_execution() -> None:
    """Verify a valid execution passes validation."""

    validate_execution(create_test_execution())


@pytest.mark.parametrize(
    "shares",
    [
        Decimal("1"),
        Decimal("0.5"),
        Decimal("0.0001"),
        Decimal("12.375"),
    ],
)
def test_valid_share_quantity(
    shares: Decimal,
) -> None:
    """Verify whole and fractional shares are supported."""

    execution = create_test_execution()
    execution.shares = shares

    validate_execution(execution)


@pytest.mark.parametrize(
    "shares",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("-0.5"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_invalid_share_quantity(
    shares: Decimal,
) -> None:
    """Verify invalid decimal share quantities are rejected."""

    execution = create_test_execution()
    execution.shares = shares

    with pytest.raises(ValueError):
        validate_execution(execution)


@pytest.mark.parametrize(
    "shares",
    [
        10,
        1.5,
        True,
        "1.25",
    ],
)
def test_shares_require_decimal(shares) -> None:
    """Verify share quantities must use Decimal."""

    execution = create_test_execution()
    execution.shares = shares

    with pytest.raises(ValueError):
        validate_execution(execution)


@pytest.mark.parametrize(
    "price",
    [
        Decimal("-1.00"),
        Decimal("0"),
        Decimal("NaN"),
        Decimal("Infinity"),
    ],
)
def test_invalid_prices(price: Decimal) -> None:
    """Verify invalid execution prices are rejected."""

    execution = create_test_execution()
    execution.price = price

    with pytest.raises(ValueError):
        validate_execution(execution)


def test_negative_execution_fee() -> None:
    """Verify negative execution fees are rejected."""

    execution = create_test_execution()
    execution.fees = Decimal("-0.01")

    with pytest.raises(ValueError):
        validate_execution(execution)


def test_naive_timestamp() -> None:
    """Verify timestamps require timezone information."""

    timestamp = datetime(2026, 9, 30, 13, 30)

    with pytest.raises(ValueError):
        validate_timestamp(timestamp)


def test_utc_normalization() -> None:
    """Verify timezone offsets normalize correctly."""

    pacific = timezone(timedelta(hours=-7))

    timestamp = datetime(
        2026,
        9,
        30,
        6,
        30,
        tzinfo=pacific,
    )

    normalized = normalize_timestamp(timestamp)

    assert normalized == datetime(
        2026,
        9,
        30,
        13,
        30,
        tzinfo=timezone.utc,
    )

    assert normalized.utcoffset() == timedelta(0)


def test_valid_deposit() -> None:
    """Verify positive deposits are accepted."""

    transaction = AccountTransaction(
        transaction_type=AccountTransactionType.DEPOSIT,
        occurred_at=datetime.now(timezone.utc),
        amount=Decimal("100.00"),
    )

    validate_account_transaction(transaction)


def test_negative_deposit() -> None:
    """Verify negative deposits are rejected."""

    transaction = AccountTransaction(
        transaction_type=AccountTransactionType.DEPOSIT,
        occurred_at=datetime.now(timezone.utc),
        amount=Decimal("-100.00"),
    )

    with pytest.raises(ValueError):
        validate_account_transaction(transaction)


def test_signed_adjustment() -> None:
    """Verify signed adjustments are supported."""

    transaction = AccountTransaction(
        transaction_type=AccountTransactionType.ADJUSTMENT,
        occurred_at=datetime.now(timezone.utc),
        amount=Decimal("-12.50"),
    )

    validate_account_transaction(transaction)


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0"),
        Decimal("0.01"),
        Decimal("12.3456"),
        Decimal("1000000.00"),
    ],
)
def test_valid_decimal(value: Decimal) -> None:
    """Verify valid nonnegative decimal values are accepted."""

    validate_decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        Decimal("-0.01"),
        Decimal("-100.00"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_invalid_decimal(value: Decimal) -> None:
    """Verify invalid financial values are rejected."""

    with pytest.raises(ValueError):
        validate_decimal(value)


def test_decimal_allow_negative() -> None:
    """Verify negative values can be explicitly permitted."""

    validate_decimal(
        Decimal("-25.50"),
        allow_negative=True,
    )


def test_decimal_disallow_zero() -> None:
    """Verify zero can be explicitly prohibited."""

    with pytest.raises(ValueError):
        validate_decimal(
            Decimal("0"),
            allow_zero=False,
        )


def test_decimal_requires_decimal_type() -> None:
    """Verify floating-point inputs are rejected."""

    with pytest.raises(ValueError):
        validate_decimal(12.50)
