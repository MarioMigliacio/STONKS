# =============================================================================
# File: test_delete_execution_dialog.py
# Purpose: Pytest file for test_delete_execution_dialog.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.delete_execution_dialog import DeleteExecutionDialog
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.trade_execution import TradeExecution


@pytest.fixture
def dialog(qtbot):
    """Create a deletion dialog for an existing BUY execution."""
    execution = TradeExecution(
        execution_id=42,
        position_id=7,
        side=ExecutionSide.BUY,
        executed_at=datetime(
            2026,
            10,
            16,
            14,
            30,
            tzinfo=timezone.utc,
        ),
        shares=Decimal("10.375"),
        price=Decimal("153.1275"),
        fees=Decimal("0.25"),
    )

    widget = DeleteExecutionDialog(
        execution=execution,
        ticker="NVDA",
    )
    qtbot.addWidget(widget)

    return widget


def test_delete_execution_dialog_displays_identity(dialog) -> None:
    """Verify the dialog identifies the selected trade."""
    text = dialog.m_details_label.text()

    assert "NVDA" in text
    assert "BUY" in text
    assert "10.375" in text
    assert "153.1275" in text
    assert "42" in text


def test_delete_execution_dialog_cancel(dialog) -> None:
    """Verify cancellation rejects the deletion request."""
    dialog.m_cancel_button.click()

    assert dialog.result() == QDialog.Rejected


def test_delete_execution_dialog_confirm(dialog) -> None:
    """Verify confirmation accepts the deletion request."""
    dialog.m_delete_button.click()

    assert dialog.result() == QDialog.Accepted
