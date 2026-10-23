# =============================================================================
# File: test_create_position_dialog.py
# Purpose: Pytest file for test_create_position_dialog.py.
# =============================================================================

from PySide6.QtWidgets import QDialog

from stonks.gui.pages.create_position_dialog import (
    CreatePositionDialog,
)
from stonks.journal.models.position import Position


def test_create_position_requires_ticker(qtbot) -> None:
    """Verify position creation requires a nonempty ticker."""
    dialog = CreatePositionDialog(
        account_id=1,
        account_name="Webull Roth IRA",
    )
    qtbot.addWidget(dialog)

    assert not dialog.m_create_button.isEnabled()

    dialog.m_ticker.setText("   ")
    assert not dialog.m_create_button.isEnabled()

    dialog.m_ticker.setText("NVDA")
    assert dialog.m_create_button.isEnabled()


def test_create_position_constructs_model(qtbot) -> None:
    """Verify form values are transferred to the Position model."""
    dialog = CreatePositionDialog(
        account_id=7,
        account_name="Webull Cash",
    )
    qtbot.addWidget(dialog)

    dialog.m_ticker.setText(" nvda ")
    dialog.m_strategy.setText("VWAP Reclaim")
    dialog.m_catalyst.setText("Positive earnings")
    dialog.m_entry_reason.setPlainText("Strong volume above VWAP.")
    dialog.m_notes.setPlainText("Waited for confirmation.")

    position = dialog.get_position()

    assert position.position_id is None
    assert position.account_id == 7
    assert position.ticker == "NVDA"
    assert position.strategy == "VWAP Reclaim"
    assert position.catalyst == "Positive earnings"
    assert position.entry_reason == "Strong volume above VWAP."
    assert position.notes == "Waited for confirmation."


def test_cancel_position_entry(qtbot) -> None:
    """Verify cancellation rejects the position entry dialog."""
    dialog = CreatePositionDialog(
        account_id=1,
        account_name="Webull Roth IRA",
    )
    qtbot.addWidget(dialog)

    dialog.m_cancel_button.click()

    assert dialog.result() == QDialog.Rejected


def test_edit_position_preserves_identity(qtbot) -> None:
    """Verify editing updates metadata without changing ownership."""
    original = Position(
        ticker="NVDA",
        position_id=42,
        account_id=7,
        strategy="Momentum",
        catalyst="Earnings",
        entry_reason="Breakout",
        notes="Original notes",
    )

    dialog = CreatePositionDialog(
        account_id=original.account_id,
        account_name="Webull Roth IRA",
        position=original,
    )
    qtbot.addWidget(dialog)

    assert dialog.m_ticker.text() == "NVDA"
    assert dialog.m_strategy.text() == "Momentum"

    dialog.m_strategy.setText("VWAP Reclaim")
    dialog.m_notes.setPlainText("Waited for confirmation")

    updated = dialog.get_position()

    assert updated.position_id == 42
    assert updated.account_id == 7
    assert updated.strategy == "VWAP Reclaim"
    assert updated.notes == "Waited for confirmation"
