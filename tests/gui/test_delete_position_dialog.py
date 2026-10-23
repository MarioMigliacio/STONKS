# =============================================================================
# File: test_delete_position_dialog.py
# Purpose: Pytest file for test_delete_position_dialog.py.
# =============================================================================

from PySide6.QtWidgets import QDialog

from stonks.gui.pages.delete_position_dialog import DeletePositionDialog
from stonks.journal.models.position import Position


def test_delete_position_dialog_displays_identity(qtbot) -> None:
    """Verify deletion confirmation identifies the selected position."""
    position = Position(
        ticker="NVDA",
        position_id=42,
        account_id=1,
    )

    dialog = DeletePositionDialog(position=position)
    qtbot.addWidget(dialog)

    assert dialog.m_position.position_id == 42
    assert dialog.m_position.ticker == "NVDA"
    assert dialog.m_delete_button.text() == "Delete Position"


def test_delete_position_dialog_cancel(qtbot) -> None:
    """Verify cancellation rejects position deletion."""
    position = Position(
        ticker="AMD",
        position_id=5,
        account_id=1,
    )

    dialog = DeletePositionDialog(position=position)
    qtbot.addWidget(dialog)

    dialog.m_cancel_button.click()

    assert dialog.result() == QDialog.Rejected


def test_delete_position_dialog_confirm(qtbot) -> None:
    """Verify confirmation accepts the deletion request."""
    position = Position(
        ticker="AMD",
        position_id=5,
        account_id=1,
    )

    dialog = DeletePositionDialog(position=position)
    qtbot.addWidget(dialog)

    dialog.m_delete_button.click()

    assert dialog.result() == QDialog.Accepted
