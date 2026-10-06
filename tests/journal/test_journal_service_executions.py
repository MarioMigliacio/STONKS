# =============================================================================
# File: test_journal_service_execution.py
# Purpose: Pytest file for test_journal_service_execution.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.position import Position
from stonks.journal.trade_execution import TradeExecution


def make_execution(
    position_id: int,
    side: ExecutionSide,
    shares: Decimal,
    minute: int = 0,
) -> TradeExecution:
    """Create a representative fractional-share execution."""

    return TradeExecution(
        position_id=position_id,
        side=side,
        executed_at=datetime(
            2026,
            9,
            30,
            13,
            30,
            tzinfo=timezone.utc,
        )
        + timedelta(minutes=minute),
        shares=shares,
        price=Decimal("165.25"),
    )


def test_create_buy(journal) -> None:
    """Verify a valid purchase is persisted."""

    service, repository, position_id = journal

    execution_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.375"),
        )
    )

    loaded = repository.get_execution(execution_id)

    assert loaded is not None
    assert loaded.shares == Decimal("1.375")


def test_partial_sell(journal) -> None:
    """Verify partial sales are permitted."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.375"),
        )
    )

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("0.375"),
            minute=1,
        )
    )

    executions = repository.get_position_executions(position_id)

    assert len(executions) == 2


def test_oversell_rolls_back(journal) -> None:
    """Verify overselling fails without storing the order."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.375"),
        )
    )

    with pytest.raises(ValueError):
        service.create_execution(
            make_execution(
                position_id,
                ExecutionSide.SELL,
                Decimal("2.000"),
                minute=1,
            )
        )

    executions = repository.get_position_executions(position_id)

    assert len(executions) == 1


def test_sell_before_buy(journal) -> None:
    """Verify an execution cannot precede its purchase."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.000"),
            minute=10,
        )
    )

    with pytest.raises(ValueError):
        service.create_execution(
            make_execution(
                position_id,
                ExecutionSide.SELL,
                Decimal("0.500"),
                minute=5,
            )
        )

    assert len(repository.get_position_executions(position_id)) == 1


def test_closed_position_cannot_reopen(journal) -> None:
    """Verify a completed trade cannot be reopened."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.500"),
        )
    )

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("1.500"),
            minute=1,
        )
    )

    with pytest.raises(ValueError):
        service.create_execution(
            make_execution(
                position_id,
                ExecutionSide.BUY,
                Decimal("0.500"),
                minute=2,
            )
        )

    assert len(repository.get_position_executions(position_id)) == 2


def test_timestamp_normalized_to_utc(journal) -> None:
    """Verify execution timestamps are stored in UTC."""

    service, repository, position_id = journal

    execution = make_execution(
        position_id,
        ExecutionSide.BUY,
        Decimal("1.25"),
    )

    execution.executed_at = datetime(
        2026,
        9,
        30,
        6,
        30,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    execution_id = service.create_execution(execution)
    loaded = repository.get_execution(execution_id)

    assert loaded is not None
    assert loaded.executed_at.utcoffset() == timedelta(0)
    assert loaded.executed_at.hour == 13


def test_invalid_fractional_quantity(journal) -> None:
    """Verify zero quantities cannot be persisted."""

    service, repository, position_id = journal

    with pytest.raises(ValueError):
        service.create_execution(
            make_execution(
                position_id,
                ExecutionSide.BUY,
                Decimal("0"),
            )
        )

    assert repository.get_position_executions(position_id) == []


def test_missing_position(journal) -> None:
    """Verify executions require an existing position."""

    service, repository, position_id = journal

    with pytest.raises(ValueError):
        service.create_execution(
            make_execution(
                999,
                ExecutionSide.BUY,
                Decimal("1.25"),
            )
        )

    assert repository.get_position_executions(position_id) == []


def test_update_execution(journal) -> None:
    """Verify an execution can be updated safely."""

    service, repository, position_id = journal

    execution_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
        )
    )

    execution = repository.get_execution(execution_id)

    assert execution is not None

    execution.shares = Decimal("12.5")

    updated = service.update_execution(execution)

    loaded = repository.get_execution(execution_id)

    assert updated is True
    assert loaded is not None
    assert loaded.shares == Decimal("12.5")


def test_update_oversell_rolls_back(journal) -> None:
    """Verify invalid historical edits are rolled back."""

    service, repository, position_id = journal

    buy_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
        )
    )

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("8"),
            minute=1,
        )
    )

    buy = repository.get_execution(buy_id)

    assert buy is not None

    buy.shares = Decimal("5")

    with pytest.raises(ValueError):
        service.update_execution(buy)

    loaded = repository.get_execution(buy_id)

    assert loaded is not None
    assert loaded.shares == Decimal("10")


def test_update_execution_timestamp_rolls_back(journal) -> None:
    """Verify backdating a SELL cannot invalidate history."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
            minute=5,
        )
    )

    sell_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("5"),
            minute=10,
        )
    )

    sell = repository.get_execution(sell_id)

    assert sell is not None

    sell.executed_at -= timedelta(minutes=10)

    with pytest.raises(ValueError):
        service.update_execution(sell)

    loaded = repository.get_execution(sell_id)

    assert loaded is not None
    assert loaded.executed_at == datetime(
        2026,
        9,
        30,
        13,
        40,
        tzinfo=timezone.utc,
    )


def test_update_execution_wrong_position(journal) -> None:
    """Verify executions cannot move between positions."""

    service, repository, position_id = journal

    execution_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
        )
    )

    with repository.m_connection:
        other_position_id = repository.create_position(Position(ticker="NVDA"))

    execution = repository.get_execution(execution_id)

    assert execution is not None

    execution.position_id = other_position_id

    with pytest.raises(ValueError):
        service.update_execution(execution)

    loaded = repository.get_execution(execution_id)

    assert loaded is not None
    assert loaded.position_id == position_id


def test_update_missing_execution(journal) -> None:
    """Verify updating an unknown execution returns False."""

    service, repository, position_id = journal

    execution = make_execution(
        position_id,
        ExecutionSide.BUY,
        Decimal("1.25"),
    )

    execution.execution_id = 999

    assert service.update_execution(execution) is False


def test_delete_execution(journal) -> None:
    """Verify a valid execution can be deleted."""

    service, repository, position_id = journal

    execution_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
        )
    )

    deleted = service.delete_execution(execution_id)

    assert deleted is True
    assert repository.get_execution(execution_id) is None


def test_delete_buy_rolls_back(journal) -> None:
    """Verify a BUY cannot be deleted if SELLs depend on it."""

    service, repository, position_id = journal

    buy_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("10"),
        )
    )

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("5"),
            minute=1,
        )
    )

    with pytest.raises(ValueError):
        service.delete_execution(buy_id)

    loaded = repository.get_execution(buy_id)

    assert loaded is not None
    assert loaded.shares == Decimal("10")


def test_delete_missing_execution(journal) -> None:
    """Verify deleting an unknown execution returns False."""

    service, repository, position_id = journal

    assert service.delete_execution(999) is False


def test_delete_sell_after_closed_position(journal) -> None:
    """Verify removing a closing SELL reopens the balance."""

    service, repository, position_id = journal

    service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.375"),
        )
    )

    sell_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.SELL,
            Decimal("1.375"),
            minute=1,
        )
    )

    assert service.delete_execution(sell_id) is True

    executions = repository.get_position_executions(position_id)

    assert len(executions) == 1
    assert executions[0].side == ExecutionSide.BUY
    assert executions[0].shares == Decimal("1.375")
