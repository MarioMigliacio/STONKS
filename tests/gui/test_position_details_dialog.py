# =============================================================================
# File: test_positions_details_dialog.py
# Purpose: Pytest file for test_positions_details_dialog.py
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

from stonks.gui.pages.position_details_dialog import PositionDetailsDialog
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount


def test_position_details_displays_executions(
    qtbot,
    tmp_path,
) -> None:
    """Verify the details dialog displays persisted trade executions."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        position_id = journal.m_service.create_position(
            Position(
                ticker="NVDA",
                account_id=account_id,
                strategy="VWAP Reclaim",
            )
        )

        journal.m_service.create_execution(
            TradeExecution(
                position_id=position_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(
                    2026,
                    10,
                    16,
                    14,
                    30,
                    tzinfo=timezone.utc,
                ),
                shares=Decimal("10"),
                price=Decimal("150"),
            )
        )

        dialog = PositionDetailsDialog(
            position_id=position_id,
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(dialog)

        assert "NVDA" in dialog.m_title.text()
        assert dialog.m_executions_table.rowCount() == 1

        assert dialog.m_executions_table.item(0, 1).text() == "BUY"
        assert dialog.m_executions_table.item(0, 2).text() == "10"
