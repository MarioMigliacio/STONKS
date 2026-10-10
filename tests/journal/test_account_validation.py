# =============================================================================
# File: test_account_validation.py
# Purpose: Pytest file for test_account_validation.py.
# =============================================================================

import pytest

from stonks.journal.account_type import AccountType
from stonks.journal.account_validation import validate_trading_account
from stonks.journal.trading_account import TradingAccount


def make_account(**overrides) -> TradingAccount:
    """
    Construct a trading account with optional field overrides.

    Args:
        **overrides:
            Account field values to override.

    Returns:
        TradingAccount:
            Account populated with test data.
    """
    values = {
        "name": "Primary IRA",
        "account_type": AccountType.ROTH_IRA,
        "broker": "Webull",
    }

    values.update(overrides)
    return TradingAccount(**values)


def test_valid_trading_account() -> None:
    """Verify valid trading account data passes validation."""

    validate_trading_account(make_account())


@pytest.mark.parametrize(
    "name",
    ["", "   ", None, 123],
)
def test_invalid_account_name(name) -> None:
    """Verify empty or invalid account names are rejected."""

    with pytest.raises(ValueError, match="Account name"):
        validate_trading_account(make_account(name=name))


def test_invalid_account_type() -> None:
    """Verify unsupported account types are rejected."""

    with pytest.raises(ValueError, match="Invalid account type"):
        validate_trading_account(make_account(account_type="ROTH_IRA"))


def test_invalid_broker() -> None:
    """Verify broker information must be a string."""

    with pytest.raises(ValueError, match="Account broker"):
        validate_trading_account(make_account(broker=None))


@pytest.mark.parametrize(
    "account_id",
    [0, -1, True, "1"],
)
def test_invalid_account_id(account_id) -> None:
    """Verify account identifiers must be positive integers."""

    with pytest.raises(ValueError, match="Account ID"):
        validate_trading_account(make_account(account_id=account_id))


@pytest.mark.parametrize(
    "field",
    ["is_active", "is_default"],
)
def test_invalid_account_flags(field) -> None:
    """Verify account state flags must be boolean values."""

    with pytest.raises(ValueError, match="must be a boolean"):
        validate_trading_account(make_account(**{field: 1}))


def test_inactive_default_account() -> None:
    """Verify an inactive account cannot be the default."""

    with pytest.raises(ValueError, match="inactive account"):
        validate_trading_account(make_account(is_active=False, is_default=True))


def test_inactive_nondefault_account() -> None:
    """Verify an inactive account is valid when not the default."""

    validate_trading_account(make_account(is_active=False, is_default=False))
