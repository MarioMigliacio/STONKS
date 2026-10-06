# =============================================================================
# File: test_journal_service_positions.py
# Purpose: Pytest file for test_journal_service_positions.py.
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


def test_create_position(journal) -> None:
    """Verify positions are normalized and persisted."""

    service, repository, _ = journal

    position_id = service.create_position(Position(ticker=" amd "))

    loaded = repository.get_position(position_id)

    assert loaded is not None
    assert loaded.ticker == "AMD"


@pytest.mark.parametrize(
    "ticker",
    ["", " ", "\t", None, 123],
)
def test_invalid_position_ticker(
    journal,
    ticker,
) -> None:
    """Verify invalid tickers are rejected."""

    service, repository, _ = journal

    with pytest.raises(ValueError):
        service.create_position(Position(ticker=ticker))


def test_update_position(journal) -> None:
    """Verify position annotations can be updated."""

    service, repository, position_id = journal

    position = repository.get_position(position_id)

    assert position is not None

    position.strategy = "Momentum"
    position.entry_reason = "Strong catalyst"

    assert service.update_position(position) is True

    loaded = repository.get_position(position_id)

    assert loaded is not None
    assert loaded.strategy == "Momentum"
    assert loaded.entry_reason == "Strong catalyst"


def test_update_closed_position_notes(journal) -> None:
    """Verify closed positions permit journal corrections."""

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
            Decimal("1.375"),
            minute=1,
        )
    )

    position = repository.get_position(position_id)

    assert position is not None

    position.lessons_learned = "Avoid chasing entries"

    assert service.update_position(position) is True

    loaded = repository.get_position(position_id)

    assert loaded is not None
    assert loaded.lessons_learned == "Avoid chasing entries"


def test_update_missing_position(journal) -> None:
    """Verify missing positions return False."""

    service, repository, _ = journal

    assert (
        service.update_position(
            Position(
                position_id=999,
                ticker="AMD",
            )
        )
        is False
    )


def test_update_position_without_id(journal) -> None:
    """Verify unsaved positions cannot be updated."""

    service, repository, _ = journal

    with pytest.raises(ValueError):
        service.update_position(Position(ticker="AMD"))


def test_delete_empty_position(journal) -> None:
    """Verify draft positions can be deleted."""

    service, repository, position_id = journal

    assert service.delete_position(position_id) is True

    assert repository.get_position(position_id) is None


def test_delete_position_with_executions(journal) -> None:
    """Verify deleting trade history is prohibited."""

    service, repository, position_id = journal

    execution_id = service.create_execution(
        make_execution(
            position_id,
            ExecutionSide.BUY,
            Decimal("1.375"),
        )
    )

    with pytest.raises(ValueError):
        service.delete_position(position_id)

    assert repository.get_position(position_id) is not None
    assert repository.get_execution(execution_id) is not None


def test_delete_missing_position(journal) -> None:
    """Verify deleting a missing position returns False."""

    service, repository, _ = journal

    assert service.delete_position(999) is False
