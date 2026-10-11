# =============================================================================
# File: test_trade_account.py
# Purpose: Pytest file for test_trade_account.py.
# =============================================================================

from stonks.journal.account_type import AccountType
from stonks.journal.trading_account import TradingAccount


def test_create_trading_account() -> None:
    """Verify a trading account stores its identifying information."""

    account = TradingAccount(
        name="Primary IRA",
        account_type=AccountType.ROTH_IRA,
        broker="Webull",
    )

    assert account.name == "Primary IRA"
    assert account.account_type == AccountType.ROTH_IRA
    assert account.broker == "Webull"
    assert account.account_id is None
    assert account.is_active is True
    assert account.is_default is False


def test_default_trading_account() -> None:
    """Verify an account can be marked as the preferred account."""

    account = TradingAccount(
        name="Primary IRA",
        account_type=AccountType.ROTH_IRA,
        is_default=True,
    )

    assert account.is_default is True


def test_inactive_trading_account() -> None:
    """Verify an account can represent an archived account."""

    account = TradingAccount(
        name="Old Brokerage Account",
        account_type=AccountType.CASH,
        is_active=False,
    )

    assert account.is_active is False
