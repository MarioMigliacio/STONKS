# =============================================================================
# File: account_validation.py
# Purpose: Validates trading account data and business rules.
# =============================================================================

from stonks.journal.account_type import AccountType
from stonks.journal.trading_account import TradingAccount


def validate_trading_account(account: TradingAccount) -> None:
    """
    Validate the fields and state of a trading account.

    Args:
        account:
            Trading account to validate.

    Raises:
        ValueError:
            If the account contains invalid data or an invalid state.
    """
    if not isinstance(account.name, str) or not account.name.strip():
        raise ValueError("Account name must be a non-empty string.")

    if not isinstance(account.account_type, AccountType):
        raise ValueError("Invalid account type.")

    if not isinstance(account.broker, str):
        raise ValueError("Account broker must be a string.")

    if account.account_id is not None:
        if type(account.account_id) is not int or account.account_id <= 0:
            raise ValueError("Account ID must be a positive integer.")

    if not isinstance(account.is_active, bool):
        raise ValueError("Account active status must be a boolean.")

    if not isinstance(account.is_default, bool):
        raise ValueError("Account default status must be a boolean.")

    if account.is_default and not account.is_active:
        raise ValueError("An inactive account cannot be the default account.")
