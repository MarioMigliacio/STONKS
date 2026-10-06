# =============================================================================
# File: test_trade_execution.py
# Purpose: Pytest file for test_trade_execution.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.trade_execution import TradeExecution


def create_execution(
    side: ExecutionSide,
    shares: Decimal = Decimal("10"),
    price: Decimal = Decimal("12.50"),
    fees: Decimal = Decimal("0.25"),
) -> TradeExecution:
    """
    Create a trade execution for testing.

    Args:
        side:
            BUY or SELL execution direction.

        shares:
            Number of executed shares.

        price:
            Execution price per share.

        fees:
            Execution fees.

    Returns:
        TradeExecution:
            Constructed execution instance.
    """
    return TradeExecution(
        position_id=1,
        side=side,
        executed_at=datetime(
            2026,
            9,
            30,
            9,
            30,
            tzinfo=timezone.utc,
        ),
        shares=shares,
        price=price,
        fees=fees,
    )


def test_create_execution() -> None:
    """Verify execution fields and default values."""

    execution = create_execution(ExecutionSide.BUY)

    assert execution.execution_id is None
    assert execution.position_id == 1
    assert execution.side == ExecutionSide.BUY
    assert execution.shares == Decimal("10")
    assert execution.price == Decimal("12.50")
    assert execution.notes == ""


def test_gross_value() -> None:
    """Verify gross transaction value."""

    execution = create_execution(ExecutionSide.BUY)

    assert execution.gross_value == Decimal("125.00")


def test_buy_cash_flow() -> None:
    """Verify purchases reduce cash including fees."""

    execution = create_execution(ExecutionSide.BUY)

    assert execution.net_cash_flow == Decimal("-125.25")


def test_sell_cash_flow() -> None:
    """Verify sales increase cash after fees."""

    execution = create_execution(ExecutionSide.SELL)

    assert execution.net_cash_flow == Decimal("124.75")


def test_execution_preserves_precision() -> None:
    """Verify fractional execution prices retain precision."""

    execution = create_execution(
        ExecutionSide.BUY,
        shares=Decimal("3"),
        price=Decimal("12.3456"),
        fees=Decimal("0.01"),
    )

    assert execution.gross_value == Decimal("37.0368")
    assert execution.net_cash_flow == Decimal("-37.0468")


def test_fractional_execution() -> None:
    """Verify fractional quantities preserve precision."""

    execution = create_execution(
        ExecutionSide.BUY,
        shares=Decimal("1.25"),
        price=Decimal("12.50"),
        fees=Decimal("0.25"),
    )

    assert execution.shares == Decimal("1.25")
    assert execution.gross_value == Decimal("15.6250")
    assert execution.net_cash_flow == Decimal("-15.8750")


def test_invalid_side_cash_flow() -> None:
    """Verify unsupported directions cannot calculate cash flow."""

    execution = create_execution(ExecutionSide.BUY)
    execution.side = "INVALID"

    with pytest.raises(ValueError):
        _ = execution.net_cash_flow
