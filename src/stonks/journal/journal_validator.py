# =============================================================================
# File: journal_validator.py
# Purpose: Validates historical journal data without modifying records.
# =============================================================================

from collections import defaultdict
from datetime import datetime
from math import isfinite

from stonks.journal.trade_order import TradeOrder


def validate_position_balances(
    orders: list[TradeOrder],
) -> list[str]:
    """
    Identify positions with inconsistent share balances.

    Calculates the remaining shares for each position
    using recorded BUY and SELL orders.

    Args:
        orders:
            Trade orders to inspect.

    Returns:
        list[str]:
            Validation warnings for positions with
            negative remaining share balances.
    """
    balances: dict[int, int] = defaultdict(int)
    warnings: list[str] = []

    for order in orders:
        if order.order_type == "BUY":
            balances[order.position_id] += order.shares

        elif order.order_type == "SELL":
            balances[order.position_id] -= order.shares

    for position_id, balance in balances.items():
        if balance < 0:
            warnings.append(f"Position {position_id}: negative share balance ({balance}).")

    return warnings


def validate_orders(
    orders: list[TradeOrder],
) -> list[str]:
    """
    Validate individual trade order records.

    Checks identifiers, order directions, execution values,
    dates, timestamps, and duplicate order identifiers.
    Does not modify the supplied records.

    Args:
        orders:
            Trade orders to validate.

    Returns:
        list[str]:
            Validation warnings describing invalid or
            inconsistent order records.
    """
    warnings: list[str] = []
    seen_ids: set[tuple[int, int]] = set()

    for order in orders:
        identifier = (order.position_id, order.order_id)
        prefix = f"Position {order.position_id}, Order {order.order_id}"

        if identifier in seen_ids:
            warnings.append(f"{prefix}: duplicate order identifier.")

        seen_ids.add(identifier)

        if order.order_id <= 0 or order.position_id <= 0:
            warnings.append(f"{prefix}: identifiers must be positive.")

        if order.order_type not in ("BUY", "SELL"):
            warnings.append(f"{prefix}: invalid order type.")

        if order.shares <= 0:
            warnings.append(f"{prefix}: shares must be positive.")

        if not isfinite(order.fill_price) or order.fill_price <= 0:
            warnings.append(f"{prefix}: invalid fill price.")

        if not isfinite(order.order_total) or order.order_total < 0:
            warnings.append(f"{prefix}: invalid order total.")

        if isfinite(order.fill_price) and isfinite(order.order_total) and order.shares > 0:
            expected_total = order.fill_price * order.shares

            if abs(order.order_total - expected_total) > 0.01:
                warnings.append(f"{prefix}: order total does not match price multiplied by shares.")

        try:
            datetime.strptime(order.trade_date, "%Y-%m-%d")
        except ValueError:
            warnings.append(f"{prefix}: invalid trade date.")

        try:
            datetime.strptime(order.time_issued, "%H:%M:%S")
        except ValueError:
            warnings.append(f"{prefix}: invalid execution time.")

    return warnings


def validate_positions(
    orders: list[TradeOrder],
) -> list[str]:
    """
    Validate chronological execution activity within positions.

    Groups orders by position, checks ticker consistency,
    identifies out-of-order records, and detects sales
    exceeding available shares at execution time.

    Assumes long-only positions and local execution timestamps.

    Args:
        orders:
            Trade orders to inspect in their stored CSV order.

    Returns:
        list[str]:
            Validation warnings describing inconsistent
            position activity.
    """
    warnings: list[str] = []
    positions: dict[int, list[TradeOrder]] = {}

    for order in orders:
        positions.setdefault(order.position_id, []).append(order)

    for position_id, position_orders in positions.items():
        tickers = {order.ticker for order in position_orders}

        if len(tickers) > 1:
            warnings.append(f"Position {position_id}: multiple tickers detected.")

        previous_timestamp = None

        for order in position_orders:
            try:
                timestamp = datetime.strptime(
                    f"{order.trade_date} {order.time_issued}",
                    "%Y-%m-%d %H:%M:%S",
                )
            except ValueError:
                continue

            if previous_timestamp is not None and timestamp < previous_timestamp:
                warnings.append(f"Position {position_id}: orders are not in chronological order.")
                break

            previous_timestamp = timestamp

        # Validate execution balances chronologically rather
        # than relying on the original CSV row order.
        chronological_orders = sorted(
            position_orders,
            key=lambda order: (
                order.trade_date,
                order.time_issued,
            ),
        )

        balance = 0

        for order in chronological_orders:
            if order.order_type == "BUY":
                balance += order.shares

            elif order.order_type == "SELL":
                balance -= order.shares

                if balance < 0:
                    warnings.append(
                        f"Position {position_id}, "
                        f"Order {order.order_id}: "
                        f"sale exceeds available shares "
                        f"({balance} remaining)."
                    )

    return warnings
