# =============================================================================
# File: test_position_analytics_integration.py
# Purpose: Pytest file for test_position_analytics_integration.py.
# =============================================================================

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from stonks.journal.execution_side import ExecutionSide
from stonks.journal.journal_database import (
    create_connection,
    initialize_database,
)
from stonks.journal.journal_repository import JournalRepository
from stonks.journal.journal_service import JournalService
from stonks.journal.position import Position
from stonks.journal.position_analytics import (
    calculate_position_metrics,
)
from stonks.journal.position_status import PositionStatus
from stonks.journal.trade_execution import TradeExecution


def test_persisted_position_analytics(tmp_path) -> None:
    """
    Verify analytics calculations using persisted journal data.
    """
    database_path = tmp_path / "journal.db"

    initialize_database(database_path)

    connection = create_connection(database_path)

    try:
        repository = JournalRepository(connection)
        service = JournalService(connection)

        position_id = service.create_position(
            Position(
                ticker="NVDA",
                strategy="Momentum",
                catalyst="Positive earnings",
            )
        )

        opened_at = datetime(2026, 10, 7, 14, 30, tzinfo=timezone.utc)

        service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=opened_at,
                shares=Decimal("10"),
                price=Decimal("100"),
                fees=Decimal("2"),
            )
        )

        service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=opened_at + timedelta(minutes=5),
                shares=Decimal("5"),
                price=Decimal("110"),
                fees=Decimal("1"),
            )
        )

        service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.SELL,
                executed_at=opened_at + timedelta(minutes=17),
                shares=Decimal("15"),
                price=Decimal("120"),
                fees=Decimal("3"),
            )
        )

        executions = repository.get_position_executions(position_id)

        metrics = calculate_position_metrics(
            position_id=position_id,
            executions=executions,
        )

        assert metrics.position_id == position_id
        assert metrics.status == PositionStatus.CLOSED
        assert metrics.open_shares == Decimal("0")
        assert metrics.remaining_cost_basis == Decimal("0")

        # Purchases: $1,000 + $550 + $3 fees = $1,553
        # Sale: $1,800 - $3 fees = $1,797
        # Realized profit: $244
        assert metrics.realized_pnl == Decimal("244")

        assert metrics.realized_return_pct == (Decimal("244") / Decimal("1553") * Decimal("100"))

        assert metrics.opened_at == opened_at
        assert metrics.closed_at == (opened_at + timedelta(minutes=17))
        assert metrics.holding_duration == timedelta(minutes=17)

    finally:
        connection.close()
