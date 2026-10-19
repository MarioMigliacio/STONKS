# =============================================================================
# File: test_positions_page.py
# Purpose: Pytest file for test_positions_page.py
# =============================================================================

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.create_position_dialog import (
    CreatePositionDialog,
)
from stonks.gui.pages.delete_position_dialog import DeletePositionDialog
from stonks.gui.pages.positions_page import PositionsPage
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.execution_side import ExecutionSide
from stonks.journal.models.position import Position
from stonks.journal.models.trade_execution import TradeExecution
from stonks.journal.models.trading_account import TradingAccount


@pytest.fixture
def filtered_positions_page(qtbot, tmp_path):
    """
    Create a journal page with positions in different lifecycle states.

    The primary account contains:
        NVDA: DRAFT
        AMD: OPEN
        TSLA: CLOSED

    The secondary account contains:
        NVDA: DRAFT
    """
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        primary_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        secondary_id = journal.m_service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

        nvda_id = journal.m_service.create_position(Position(ticker="NVDA", account_id=primary_id))

        amd_id = journal.m_service.create_position(Position(ticker="AMD", account_id=primary_id))

        tsla_id = journal.m_service.create_position(Position(ticker="TSLA", account_id=primary_id))

        journal.m_service.create_position(Position(ticker="NVDA", account_id=secondary_id))

        journal.m_service.create_execution(
            TradeExecution(
                position_id=amd_id,
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

        journal.m_service.create_execution(
            TradeExecution(
                position_id=tsla_id,
                side=ExecutionSide.BUY,
                executed_at=datetime(
                    2026,
                    10,
                    16,
                    14,
                    30,
                    tzinfo=timezone.utc,
                ),
                shares=Decimal("5"),
                price=Decimal("200"),
            )
        )

        journal.m_service.create_execution(
            TradeExecution(
                position_id=tsla_id,
                side=ExecutionSide.SELL,
                executed_at=datetime(
                    2026,
                    10,
                    16,
                    15,
                    30,
                    tzinfo=timezone.utc,
                ),
                shares=Decimal("5"),
                price=Decimal("210"),
            )
        )

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        yield page, primary_id, secondary_id, nvda_id


def get_visible_tickers(page: PositionsPage) -> list:
    """
    Return ticker symbols belonging to visible table rows.

    Args:
        page:
            Positions page being inspected.

    Returns:
        list:
            Ticker symbols currently visible after filtering.
    """
    return [
        page.m_table.item(row, 0).text() for row in range(page.m_table.rowCount()) if not page.m_table.isRowHidden(row)
    ]


def test_positions_page_selects_default_account(qtbot, tmp_path) -> None:
    """Verify the default trading account is selected automatically."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        default_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        journal.m_service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        assert page.get_selected_account_id() == default_id
        assert page.m_account_selector.count() == 2
        assert page.m_create_button.isEnabled()


def test_positions_page_filters_by_account(qtbot, tmp_path) -> None:
    """Verify only positions belonging to the selected account appear."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        primary_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        cash_id = journal.m_service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

        journal.m_service.create_position(Position(ticker="NVDA", account_id=primary_id))

        journal.m_service.create_position(Position(ticker="AMD", account_id=cash_id))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        # Default account displays its own positions.
        assert page.m_table.rowCount() == 1
        assert page.m_table.item(0, 0).text() == "NVDA"

        # Switch to the cash account.
        index = page.m_account_selector.findData(cash_id)
        assert index >= 0

        page.m_account_selector.setCurrentIndex(index)

        assert page.get_selected_account_id() == cash_id
        assert page.m_table.rowCount() == 1
        assert page.m_table.item(0, 0).text() == "AMD"


def test_positions_page_displays_empty_state(qtbot, tmp_path) -> None:
    """Verify empty accounts display the appropriate message."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        assert page.m_table.rowCount() == 0
        assert not page.m_empty_label.isHidden()

        # Creating a position should hide the empty-state message.
        account_id = page.get_selected_account_id()

        journal.m_service.create_position(Position(ticker="AAPL", account_id=account_id))

        page.refresh_positions()

        assert page.m_table.rowCount() == 1
        assert page.m_empty_label.isHidden()


def test_positions_page_restricts_archived_accounts(qtbot, tmp_path) -> None:
    """Verify archived accounts are viewable but cannot create positions."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        archived_id = journal.m_service.create_trading_account(TradingAccount("Old Cash", AccountType.CASH))

        position_id = journal.m_service.create_position(Position(ticker="TSLA", account_id=archived_id))

        assert journal.m_service.archive_trading_account(archived_id)

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        index = page.m_account_selector.findData(archived_id)
        assert index >= 0

        page.m_account_selector.setCurrentIndex(index)

        assert "Archived" in page.m_account_selector.currentText()
        assert not page.m_create_button.isEnabled()

        # Archived history remains accessible.
        assert page.m_table.rowCount() == 1
        assert page.m_table.item(0, 0).text() == "TSLA"
        assert page.m_table.item(0, 0).data(Qt.UserRole) == position_id


def test_positions_page_preserves_account_selection(qtbot, tmp_path) -> None:
    """Verify refreshing accounts preserves the user's selection."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        cash_id = journal.m_service.create_trading_account(TradingAccount("Cash Account", AccountType.CASH))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        index = page.m_account_selector.findData(cash_id)
        page.m_account_selector.setCurrentIndex(index)

        # Introduce another account after page creation.
        journal.m_service.create_trading_account(TradingAccount("Secondary IRA", AccountType.ROTH_IRA))

        page.refresh_accounts()

        assert page.m_account_selector.count() == 3
        assert page.get_selected_account_id() == cash_id


def test_positions_page_creates_position(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify confirmed entry creates a persisted journal position."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        def accept_position(dialog):
            dialog.m_ticker.setText("AMD")
            dialog.m_strategy.setText("VWAP Reclaim")
            return QDialog.Accepted

        monkeypatch.setattr(
            CreatePositionDialog,
            "exec",
            accept_position,
        )

        page.m_create_button.click()

        positions = journal.m_repository.get_positions(account_id=account_id)

        assert len(positions) == 1
        assert positions[0].ticker == "AMD"
        assert positions[0].strategy == "VWAP Reclaim"

        assert page.m_table.rowCount() == 1
        assert page.m_table.item(0, 0).text() == "AMD"


def test_positions_page_cancel_does_not_create(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify cancelling position entry leaves the journal unchanged."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        monkeypatch.setattr(
            CreatePositionDialog,
            "exec",
            lambda self: QDialog.Rejected,
        )

        page.m_create_button.click()

        assert journal.m_repository.get_positions(account_id) == []
        assert page.m_table.rowCount() == 0


def test_positions_page_edits_position(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify editing persists position changes through the service."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        position_id = journal.m_service.create_position(Position(ticker="NVDA", account_id=account_id))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        def accept_edit(dialog):
            dialog.m_strategy.setText("VWAP Reclaim")
            return QDialog.Accepted

        monkeypatch.setattr(
            CreatePositionDialog,
            "exec",
            accept_edit,
        )

        page.m_edit_action.trigger()

        updated = journal.m_repository.get_position(position_id)

        assert updated is not None
        assert updated.strategy == "VWAP Reclaim"
        assert updated.account_id == account_id

        assert page.get_selected_position_id() == position_id


def test_positions_page_deletes_empty_position(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify confirmed deletion removes an empty position."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        position_id = journal.m_service.create_position(Position(ticker="AMD", account_id=account_id))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        monkeypatch.setattr(
            DeletePositionDialog,
            "exec",
            lambda self: QDialog.Accepted,
        )

        page.m_delete_action.trigger()

        assert journal.m_repository.get_position(position_id) is None
        assert page.m_table.rowCount() == 0


def test_positions_page_cancel_delete(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    """Verify declining deletion preserves the position."""
    database_path = tmp_path / "journal.db"

    with JournalContext(database_path) as journal:
        account_id = journal.m_service.create_trading_account(TradingAccount("Primary IRA", AccountType.ROTH_IRA))

        position_id = journal.m_service.create_position(Position(ticker="AMD", account_id=account_id))

        page = PositionsPage(
            repository=journal.m_repository,
            service=journal.m_service,
        )
        qtbot.addWidget(page)

        page.m_table.selectRow(0)

        monkeypatch.setattr(
            DeletePositionDialog,
            "exec",
            lambda self: QDialog.Rejected,
        )

        page.m_delete_action.trigger()

        assert journal.m_repository.get_position(position_id) is not None
        assert page.m_table.rowCount() == 1


def test_positions_page_search_filters_tickers(
    filtered_positions_page,
) -> None:
    """Verify ticker searching is case-insensitive and supports substrings."""
    page, _, _, _ = filtered_positions_page

    assert set(get_visible_tickers(page)) == {
        "NVDA",
        "AMD",
        "TSLA",
    }

    page.m_search_input.setText("nv")

    assert get_visible_tickers(page) == ["NVDA"]

    page.m_search_input.setText("TS")

    assert get_visible_tickers(page) == ["TSLA"]

    page.m_search_input.clear()

    assert len(get_visible_tickers(page)) == 3


def test_positions_page_filters_by_status(
    filtered_positions_page,
) -> None:
    """Verify lifecycle filters show only matching positions."""
    page, _, _, _ = filtered_positions_page

    expected_results = {
        "DRAFT": "NVDA",
        "OPEN": "AMD",
        "CLOSED": "TSLA",
    }

    for status, expected_ticker in expected_results.items():
        index = page.m_status_filter.findData(status)

        assert index >= 0

        page.m_status_filter.setCurrentIndex(index)

        assert get_visible_tickers(page) == [expected_ticker]

    page.m_status_filter.setCurrentIndex(0)

    assert len(get_visible_tickers(page)) == 3


def test_positions_page_combines_search_and_status(
    filtered_positions_page,
) -> None:
    """Verify ticker search and lifecycle filtering work together."""
    page, _, _, _ = filtered_positions_page

    page.m_search_input.setText("AMD")

    open_index = page.m_status_filter.findData("OPEN")
    page.m_status_filter.setCurrentIndex(open_index)

    assert get_visible_tickers(page) == ["AMD"]

    closed_index = page.m_status_filter.findData("CLOSED")
    page.m_status_filter.setCurrentIndex(closed_index)

    assert get_visible_tickers(page) == []
    assert not page.m_empty_label.isHidden()

    assert page.m_empty_label.text() == "No positions match your current search or filters."

    page.m_status_filter.setCurrentIndex(open_index)

    assert get_visible_tickers(page) == ["AMD"]
    assert page.m_empty_label.isHidden()


def test_positions_page_hidden_selection_disables_actions(
    filtered_positions_page,
) -> None:
    """Verify filtering out a selected position prevents stale actions."""
    page, _, _, nvda_id = filtered_positions_page

    nvda_row = next(row for row in range(page.m_table.rowCount()) if page.m_table.item(row, 0).text() == "NVDA")

    page.m_table.selectRow(nvda_row)

    assert page.get_selected_position_id() == nvda_id
    assert page.m_actions_button.isEnabled()

    page.m_search_input.setText("AMD")

    assert get_visible_tickers(page) == ["AMD"]
    assert page.get_selected_position_id() is None
    assert not page.m_actions_button.isEnabled()
    assert not page.m_edit_action.isEnabled()
    assert not page.m_delete_action.isEnabled()


def test_positions_page_preserves_filters_between_accounts(
    filtered_positions_page,
) -> None:
    """Verify search and status selections persist across account changes."""
    page, primary_id, secondary_id, _ = filtered_positions_page

    page.m_search_input.setText("NVDA")

    draft_index = page.m_status_filter.findData("DRAFT")
    page.m_status_filter.setCurrentIndex(draft_index)

    assert get_visible_tickers(page) == ["NVDA"]

    secondary_index = page.m_account_selector.findData(secondary_id)

    page.m_account_selector.setCurrentIndex(secondary_index)

    assert page.get_selected_account_id() == secondary_id
    assert page.m_search_input.text() == "NVDA"
    assert page.m_status_filter.currentData() == "DRAFT"
    assert get_visible_tickers(page) == ["NVDA"]

    primary_index = page.m_account_selector.findData(primary_id)

    page.m_account_selector.setCurrentIndex(primary_index)

    assert page.get_selected_account_id() == primary_id
    assert get_visible_tickers(page) == ["NVDA"]
