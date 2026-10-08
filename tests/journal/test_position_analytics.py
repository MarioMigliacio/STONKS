# =============================================================================
# File: test_position_analytics.py
# Purpose: Pytest file for test_position_analytics.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position_analytics import (
    calculate_position_metrics,
)
from stonks.journal.position_status import PositionStatus
from stonks.journal.trade_execution import TradeExecution


def make_execution(
    side: ExecutionSide,
    shares: str,
    price: str,
    fees: str = "0",
    executed_at: Optional[datetime] = None,
) -> TradeExecution:
    """Create a trading execution for analytics tests."""

    return TradeExecution(
        position_id=1,
        side=side,
        executed_at=(executed_at if executed_at is not None else datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc)),
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


def test_draft_position_status() -> None:
    """Verify positions without executions remain drafts."""

    metrics = calculate_position_metrics(1, [])

    assert metrics.status == PositionStatus.DRAFT
    assert metrics.realized_return_pct is None


def test_open_position_status() -> None:
    """Verify positions with remaining shares are open."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.status == PositionStatus.OPEN
    assert metrics.realized_return_pct is None


def test_closed_position_realized_return() -> None:
    """Verify realized return for a fully closed position."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.SELL, "10", "120"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.status == PositionStatus.CLOSED
    assert metrics.realized_return_pct == Decimal("20")


def test_partial_sale_realized_return() -> None:
    """Verify realized return uses only sold-share cost basis."""

    executions = [
        make_execution(ExecutionSide.BUY, "10", "100"),
        make_execution(ExecutionSide.SELL, "5", "120"),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.status == PositionStatus.OPEN
    assert metrics.realized_return_pct == Decimal("20")


def test_draft_position_has_no_holding_duration() -> None:
    """Verify draft positions have no holding timestamps."""

    metrics = calculate_position_metrics(1, [])

    assert metrics.opened_at is None
    assert metrics.closed_at is None
    assert metrics.holding_duration is None


def test_open_position_has_no_holding_duration() -> None:
    """Verify open positions have no completed holding duration."""

    opened_at = datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc)

    executions = [
        make_execution(
            ExecutionSide.BUY,
            "10",
            "100",
            executed_at=opened_at,
        ),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.opened_at == opened_at
    assert metrics.closed_at is None
    assert metrics.holding_duration is None


def test_closed_position_holding_duration() -> None:
    """Verify duration between first purchase and final sale."""

    opened_at = datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc)

    closed_at = datetime(2026, 10, 7, 14, 47, tzinfo=timezone.utc)

    executions = [
        make_execution(
            ExecutionSide.BUY,
            "10",
            "100",
            executed_at=opened_at,
        ),
        make_execution(
            ExecutionSide.SELL,
            "10",
            "120",
            executed_at=closed_at,
        ),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.opened_at == opened_at
    assert metrics.closed_at == closed_at
    assert metrics.holding_duration == timedelta(minutes=17)


def test_partial_exit_does_not_end_holding_duration() -> None:
    """Verify partial exits leave the position open."""

    opened_at = datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc)

    partial_exit_at = datetime(2026, 10, 7, 14, 45, tzinfo=timezone.utc)

    executions = [
        make_execution(
            ExecutionSide.BUY,
            "10",
            "100",
            executed_at=opened_at,
        ),
        make_execution(
            ExecutionSide.SELL,
            "5",
            "120",
            executed_at=partial_exit_at,
        ),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.opened_at == opened_at
    assert metrics.closed_at is None
    assert metrics.holding_duration is None


def test_holding_duration_across_timezones() -> None:
    """Verify duration calculations across timezone offsets."""

    pacific = timezone(timedelta(hours=-7))

    opened_at = datetime(2026, 10, 7, 7, 30, tzinfo=pacific)

    closed_at = datetime(2026, 10, 7, 14, 47, tzinfo=timezone.utc)

    executions = [
        make_execution(
            ExecutionSide.BUY,
            "10",
            "100",
            executed_at=opened_at,
        ),
        make_execution(
            ExecutionSide.SELL,
            "10",
            "120",
            executed_at=closed_at,
        ),
    ]

    metrics = calculate_position_metrics(1, executions)

    assert metrics.holding_duration == timedelta(minutes=17)
