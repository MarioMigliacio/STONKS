# =============================================================================
# File: test_positions_page.py
# Purpose: Pytest file for test_positions_page.py
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog

from stonks.gui.pages.create_position_dialog import (
    CreatePositionDialog,
)
from stonks.gui.pages.delete_position_dialog import DeletePositionDialog
from stonks.gui.pages.positions_page import PositionsPage
from stonks.journal.journal_context import JournalContext
from stonks.journal.models.account_type import AccountType
from stonks.journal.models.position import Position
from stonks.journal.models.trading_account import TradingAccount


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
