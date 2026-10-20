# =============================================================================
# File: test_delete_account_dialog.py
# Purpose: Pytest file for test_delete_account_dialog.py.
# =============================================================================

from PySide6.QtWidgets import QDialog

from stonks.gui.pages.delete_account_dialog import DeleteAccountDialog


def test_delete_button_requires_exact_account_name(qtbot) -> None:
    """Verify deletion requires an exact account-name match."""
    dialog = DeleteAccountDialog(
        account_name="Old Cash",
        summary={
            "positions": 2,
            "executions": 5,
            "transactions": 3,
        },
    )
    qtbot.addWidget(dialog)

    assert not dialog.m_delete_button.isEnabled()

    dialog.m_confirmation_input.setText("Old")
    assert not dialog.m_delete_button.isEnabled()

    dialog.m_confirmation_input.setText("old cash")
    assert not dialog.m_delete_button.isEnabled()

    dialog.m_confirmation_input.setText("Old Cash")
    assert dialog.m_delete_button.isEnabled()

    dialog.m_confirmation_input.clear()
    assert not dialog.m_delete_button.isEnabled()


def test_delete_dialog_can_be_cancelled(qtbot) -> None:
    """Verify cancellation rejects the deletion dialog."""
    dialog = DeleteAccountDialog(
        account_name="Old Cash",
        summary={
            "positions": 1,
            "executions": 2,
            "transactions": 1,
        },
    )
    qtbot.addWidget(dialog)

    dialog.m_cancel_button.click()

    assert dialog.result() == QDialog.Rejected


def test_delete_dialog_accepts_exact_confirmation(qtbot) -> None:
    """Verify exact account-name confirmation authorizes deletion."""
    dialog = DeleteAccountDialog(
        account_name="Old Cash",
        summary={
            "positions": 1,
            "executions": 2,
            "transactions": 1,
        },
    )
    qtbot.addWidget(dialog)

    dialog.m_confirmation_input.setText("Old Cash")
    dialog.m_delete_button.click()

    assert dialog.result() == QDialog.Accepted
