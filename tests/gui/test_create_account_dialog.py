# =============================================================================
# File: test_create_account_dialog.py
# Purpose: Pytest file for test_create_account_dialog.py.
# =============================================================================

import pytest

from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.trading_account import TradingAccount


@pytest.mark.parametrize("account_type", list(AccountType))
def test_create_account_dialog_builds_account(
    qtbot,
    account_type: AccountType,
) -> None:
    """Verify all account types are preserved when creating accounts."""
    dialog = CreateAccountDialog()
    qtbot.addWidget(dialog)

    dialog.m_name.setText("Test Account")
    dialog.m_broker.setText("Webull")

    index = dialog.m_account_type.findData(account_type.value)

    assert index >= 0

    dialog.m_account_type.setCurrentIndex(index)

    account = dialog.get_account()

    assert account.name == "Test Account"
    assert account.account_type is account_type
    assert account.broker == "Webull"


def test_edit_dialog_populates_existing_account(qtbot) -> None:
    """Verify editing a trading account populates its existing values."""
    account = TradingAccount(
        name="Webull Cash",
        account_type=AccountType.CASH,
        broker="Webull",
        account_id=42,
        is_active=True,
        is_default=False,
    )

    dialog = CreateAccountDialog(account=account)
    qtbot.addWidget(dialog)

    assert dialog.m_name.text() == "Webull Cash"
    assert dialog.m_broker.text() == "Webull"

    assert dialog.m_account_type.currentData() == AccountType.CASH.value


def test_edit_dialog_preserves_account_identity(qtbot) -> None:
    """Verify account editing preserves database identity and state."""
    account = TradingAccount(
        name="Webull Roth IRA",
        account_type=AccountType.ROTH_IRA,
        broker="Webull",
        account_id=7,
        is_active=True,
        is_default=True,
    )

    dialog = CreateAccountDialog(account=account)
    qtbot.addWidget(dialog)

    dialog.m_name.setText("Retirement Account")
    dialog.m_broker.setText("Updated Broker")

    updated_account = dialog.get_account()

    assert updated_account.name == "Retirement Account"
    assert updated_account.broker == "Updated Broker"

    assert updated_account.account_id == 7
    assert updated_account.is_active is True
    assert updated_account.is_default is True
    assert updated_account.account_type is AccountType.ROTH_IRA
