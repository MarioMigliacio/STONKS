# =============================================================================
# File: test_position_analytics.py
# Purpose: Pytest file for test_position_analytics.py.
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position_analytics import (
    calculate_position_metrics,
)
from stonks.journal.trade_execution import TradeExecution


def make_execution(
    side: ExecutionSide,
    shares: str,
    price: str,
    fees: str = "0",
) -> TradeExecution:
    """Create a trading execution for analytics tests."""

    return TradeExecution(
        position_id=1,
        side=side,
        executed_at=datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc),
        shares=Decimal(shares),
        price=Decimal(price),
        fees=Decimal(fees),
    )


def test_empty_position_metrics() -> None:
    """Verify a position without executions has no entry price."""

    metrics = calculate_position_metrics(
        position_id=1,
        executions=[],
    )

    assert metrics.open_shares == Decimal("0")
    assert metrics.average_entry_price is None


def test_single_purchase_metrics() -> None:
    """Verify metrics for a single purchase."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.open_shares == Decimal("10")
    assert metrics.average_entry_price == Decimal("100")


def test_multiple_purchases_weighted_average() -> None:
    """Verify average entry price is weighted by shares."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.BUY, "5", "110"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.open_shares == Decimal("15")
    assert metrics.average_entry_price == (Decimal("1550") / Decimal("15"))


def test_partial_sale_reduces_open_shares() -> None:
    """Verify partial sales reduce the remaining share balance."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.BUY, "5", "110"),
        make_execution(ExecutionSide.SELL, "8", "120"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.open_shares == Decimal("7")
    assert metrics.average_entry_price == (Decimal("1550") / Decimal("15"))


def test_partial_sale_realized_pnl() -> None:
    """Verify partial sales realize weighted-average profit."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.BUY, "5", "110"),
        make_execution(ExecutionSide.SELL, "8", "120"),
    ]

    metrics = calculate_position_metrics(1, executions)

    expected_cost_sold = Decimal("1550") * Decimal("8") / Decimal("15")

    expected_pnl = Decimal("960") - expected_cost_sold

    assert metrics.open_shares == Decimal("7")
    assert metrics.realized_pnl == expected_pnl
    assert metrics.remaining_cost_basis == (Decimal("1550") - expected_cost_sold)


def test_full_exit_realized_pnl() -> None:
    """Verify closing a position clears its remaining cost basis."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.SELL, "10", "120"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.open_shares == Decimal("0")
    assert metrics.average_entry_price is None
    assert metrics.remaining_cost_basis == Decimal("0")
    assert metrics.realized_pnl == Decimal("200")


def test_realized_pnl_includes_fees() -> None:
    """Verify purchase and selling fees reduce realized profit."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100", "2.00"),
        make_execution(ExecutionSide.SELL, "10", "120", "3.00"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.realized_pnl == Decimal("195.00")
    assert metrics.remaining_cost_basis == Decimal("0")


def test_purchase_after_partial_sale() -> None:
    """Verify later purchases update the remaining average cost."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.SELL, "5", "120"),
        make_execution(ExecutionSide.BUY, "5", "140"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.open_shares == Decimal("10")
    assert metrics.average_entry_price == Decimal("120")
    assert metrics.remaining_cost_basis == Decimal("1200")
    assert metrics.realized_pnl == Decimal("100")
