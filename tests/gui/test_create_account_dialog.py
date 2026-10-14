# =============================================================================
# File: test_create_account_dialog.py
# Purpose: Pytest file for test_create_account_dialog.py.
# =============================================================================

import pytest

from stonks.gui.pages.create_account_dialog import CreateAccountDialog
from stonks.journal.models.account_type import AccountType


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
