# =============================================================================
# File: test_journal_validator.py
# Purpose: Pytest file for journal_validator.py.
# =============================================================================

from stonks.journal.journal_validator import validate_orders, validate_position_balances, validate_positions
from stonks.journal.trade_order import TradeOrder


def create_order(
    order_id: int,
    position_id: int,
    order_type: str,
    shares: int,
) -> TradeOrder:
    """
    Create a trade order with default values for testing.

    Args:
        order_id:
            Sequence identifier for the order.

        position_id:
            Identifier grouping related orders.

        order_type:
            Trade direction, BUY or SELL.

        shares:
            Number of shares executed.

    Returns:
        TradeOrder:
            A trade order populated with test data.
    """
    return TradeOrder(
        order_id=order_id,
        position_id=position_id,
        trade_date="2026-06-03",
        ticker="TEST",
        order_type=order_type,
        fill_price=10.0,
        shares=shares,
        order_total=10.0 * shares,
        time_issued="09:30:00",
    )


def test_closed_position() -> None:
    """Verify a fully closed position produces no warnings."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(2, 1, "SELL", 100),
    ]

    warnings = validate_position_balances(orders)

    assert warnings == []


def test_open_position() -> None:
    """Verify a partially open position produces no warnings."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(2, 1, "SELL", 40),
    ]

    warnings = validate_position_balances(orders)

    assert warnings == []


def test_negative_position_balance() -> None:
    """Verify overselling a position produces a warning."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(2, 1, "SELL", 120),
    ]

    warnings = validate_position_balances(orders)

    assert len(warnings) == 1
    assert "Position 1" in warnings[0]
    assert "-20" in warnings[0]


def test_multiple_positions() -> None:
    """Verify positions are validated independently."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(2, 1, "SELL", 100),
        create_order(1, 2, "BUY", 50),
        create_order(2, 2, "SELL", 75),
    ]

    warnings = validate_position_balances(orders)

    assert len(warnings) == 1
    assert "Position 2" in warnings[0]


def test_valid_order() -> None:
    """Verify a valid order produces no warnings."""

    orders = [
        create_order(1, 1, "BUY", 100),
    ]

    assert validate_orders(orders) == []


def test_duplicate_order_identifier() -> None:
    """Detect duplicate identifiers within a position."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(1, 1, "SELL", 100),
    ]

    warnings = validate_orders(orders)

    assert any("duplicate" in warning for warning in warnings)


def test_reused_order_id_across_positions() -> None:
    """Allow legacy order IDs to repeat across positions."""

    orders = [
        create_order(1, 1, "BUY", 100),
        create_order(1, 2, "BUY", 100),
    ]

    assert validate_orders(orders) == []


def test_invalid_share_quantity() -> None:
    """Reject zero or negative share quantities."""

    order = create_order(1, 1, "BUY", 0)

    warnings = validate_orders([order])

    assert any("shares" in warning for warning in warnings)


def test_invalid_order_total() -> None:
    """Detect an inconsistent execution total."""

    order = create_order(1, 1, "BUY", 100)
    order.order_total = 500.0

    warnings = validate_orders([order])

    assert any("order total" in warning for warning in warnings)


def test_invalid_order_date() -> None:
    """Detect invalid execution dates."""

    order = create_order(1, 1, "BUY", 100)
    order.trade_date = "invalid"

    warnings = validate_orders([order])

    assert any("trade date" in warning for warning in warnings)


def test_invalid_order_time() -> None:
    """Detect invalid execution timestamps."""

    order = create_order(1, 1, "BUY", 100)
    order.time_issued = "invalid"

    warnings = validate_orders([order])

    assert any("execution time" in warning for warning in warnings)


def test_position_detects_chronological_oversell() -> None:
    """Detect overselling even when later purchases restore balance."""

    buy = create_order(1, 1, "BUY", 100)
    sell = create_order(2, 1, "SELL", 120)
    later_buy = create_order(3, 1, "BUY", 20)

    buy.time_issued = "09:30:00"
    sell.time_issued = "09:35:00"
    later_buy.time_issued = "09:40:00"

    warnings = validate_positions([buy, sell, later_buy])

    assert any("sale exceeds" in warning for warning in warnings)


def test_position_detects_mixed_tickers() -> None:
    """Detect multiple ticker symbols assigned to one position."""

    first = create_order(1, 1, "BUY", 100)
    second = create_order(2, 1, "SELL", 100)
    second.ticker = "OTHER"

    warnings = validate_positions([first, second])

    assert any("multiple tickers" in warning for warning in warnings)


def test_position_detects_out_of_order_records() -> None:
    """Detect orders stored out of chronological sequence."""

    first = create_order(1, 1, "BUY", 100)
    second = create_order(2, 1, "SELL", 100)

    first.time_issued = "10:00:00"
    second.time_issued = "09:30:00"

    warnings = validate_positions([first, second])

    assert any("chronological order" in warning for warning in warnings)


def test_position_allows_partial_exit() -> None:
    """Allow valid partial exits and additional purchases."""

    buy = create_order(1, 1, "BUY", 100)
    partial_sell = create_order(2, 1, "SELL", 40)
    additional_buy = create_order(3, 1, "BUY", 20)

    buy.time_issued = "09:30:00"
    partial_sell.time_issued = "09:35:00"
    additional_buy.time_issued = "09:40:00"

    warnings = validate_positions([buy, partial_sell, additional_buy])

    assert warnings == []
