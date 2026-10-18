# =============================================================================
# File: test_add_execution_dialog.py
# Purpose: Pytest file for test_add_execution_dialog.py.
# =============================================================================

from decimal import Decimal

import pytest
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.add_execution_dialog import AddExecutionDialog
from stonks.journal.models.execution_side import ExecutionSide


@pytest.fixture
def dialog(qtbot):
    """Create a trade execution entry dialog."""
    widget = AddExecutionDialog(
        position_id=42,
        ticker="NVDA",
    )
    qtbot.addWidget(widget)
    return widget


def test_add_execution_dialog_defaults_to_buy(dialog) -> None:
    """Verify the default execution direction is a valid enum."""
    dialog.m_shares.setText("10")
    dialog.m_price.setText("150")

    execution = dialog.get_execution()

    assert execution.side is ExecutionSide.BUY
    assert isinstance(execution.side, ExecutionSide)
    assert dialog.m_fees.text() == "0.00"


def test_add_execution_dialog_creates_buy(dialog) -> None:
    """Verify fractional quantities and prices retain precision."""
    dialog.m_shares.setText("10.375")
    dialog.m_price.setText("153.1275")
    dialog.m_notes.setPlainText("VWAP reclaim entry")

    execution = dialog.get_execution()

    assert execution.position_id == 42
    assert execution.side == ExecutionSide.BUY
    assert execution.shares == Decimal("10.375")
    assert execution.price == Decimal("153.1275")
    assert execution.fees == Decimal("0.00")
    assert execution.notes == "VWAP reclaim entry"
    assert execution.executed_at.utcoffset().total_seconds() == 0


def test_add_execution_dialog_creates_sell(dialog) -> None:
    """Verify the form supports SELL executions."""
    dialog.m_side.setCurrentIndex(1)
    dialog.m_shares.setText("5")
    dialog.m_price.setText("160.25")
    dialog.m_fees.setText("0.75")

    execution = dialog.get_execution()

    assert execution.side is ExecutionSide.SELL
    assert execution.shares == Decimal("5")
    assert execution.price == Decimal("160.25")
    assert execution.fees == Decimal("0.75")


@pytest.mark.parametrize(
    "shares,price,fees",
    [
        ("", "150", "0"),
        ("0", "150", "0"),
        ("-1", "150", "0"),
        ("abc", "150", "0"),
        ("10", "0", "0"),
        ("10", "NaN", "0"),
        ("10", "150", "-1"),
    ],
)
def test_add_execution_dialog_rejects_invalid_amounts(
    dialog,
    shares,
    price,
    fees,
) -> None:
    """Verify invalid financial inputs cannot create executions."""
    dialog.m_shares.setText(shares)
    dialog.m_price.setText(price)
    dialog.m_fees.setText(fees)

    with pytest.raises(ValueError):
        dialog.get_execution()


def test_add_execution_dialog_cancel(dialog) -> None:
    """Verify cancellation rejects the entry."""
    dialog.m_cancel_button.click()

    assert dialog.result() == QDialog.Rejected


def test_add_execution_dialog_confirm(dialog) -> None:
    """Verify valid entry accepts the dialog."""
    dialog.m_shares.setText("10")
    dialog.m_price.setText("150")

    dialog.m_save_button.click()

    assert dialog.result() == QDialog.Accepted
