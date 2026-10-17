# =============================================================================
# File: positions_page.py
# Purpose: Displays journal positions for the selected trading account.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.gui.icons import get_icon
from stonks.journal.persistence.journal_repository import JournalRepository
from stonks.journal.services.journal_service import JournalService


class PositionsPage(QWidget):
    """
    Display trading journal positions for a selected account.

    Provides account-aware position history, automatic default
    account selection, and controls for creating new positions.

    Archived accounts remain available for historical review,
    but cannot receive new positions.

    Attributes:
        m_repository:
            Journal repository used to retrieve accounts and positions.

        m_service:
            Optional journal service used for validated operations.

        m_account_selector:
            Dropdown containing the available trading accounts.

        m_create_button:
            Button used to begin creating a new position.

        m_table:
            Table displaying positions for the selected account.

        m_empty_label:
            Informational label displayed when no positions exist.
    """

    def __init__(
        self,
        repository: JournalRepository,
        service: Optional[JournalService] = None,
    ) -> None:
        """Initialize the positions page and load journal data."""
        super().__init__()

        self.m_repository = repository
        self.m_service = service

        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        """Construct the journal overview interface."""
        layout = QVBoxLayout(self)

        # Page header.
        header_layout = QHBoxLayout()

        title = QLabel("Trading Journal")
        title.setObjectName("pageTitle")

        self.m_create_button = QPushButton("New Position")
        self.m_create_button.setIcon(get_icon("plus"))
        self.m_create_button.setEnabled(False)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.m_create_button)

        layout.addLayout(header_layout)

        # Account selection.
        account_label = QLabel("Trading Account")

        self.m_account_selector = QComboBox()
        self.m_account_selector.currentIndexChanged.connect(self._on_account_changed)

        layout.addWidget(account_label)
        layout.addWidget(self.m_account_selector)

        # Positions table.
        self.m_table = QTableWidget()
        self.m_table.setColumnCount(4)

        self.m_table.setHorizontalHeaderLabels(
            [
                "Ticker",
                "Strategy",
                "Catalyst",
                "Position ID",
            ]
        )

        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.m_table)

        # Empty state.
        self.m_empty_label = QLabel("No positions recorded for this trading account.")
        self.m_empty_label.setObjectName("emptyState")

        layout.addWidget(self.m_empty_label)

    def refresh_accounts(self) -> None:
        """Reload account choices while preserving the current selection."""
        previous_account_id = self.get_selected_account_id()
        accounts = self.m_repository.get_trading_accounts()

        self.m_account_selector.blockSignals(True)
        self.m_account_selector.clear()

        for account in accounts:
            name = account.name

            if not account.is_active:
                name += " (Archived)"

            self.m_account_selector.addItem(
                name,
                userData=account.account_id,
            )

        # Preserve selection, or fall back to the default account.
        selected_account_id = previous_account_id

        if selected_account_id is None or not any(account.account_id == selected_account_id for account in accounts):
            default_account = next(
                (account for account in accounts if account.is_default),
                None,
            )

            selected_account_id = default_account.account_id if default_account is not None else None

        if selected_account_id is not None:
            index = self.m_account_selector.findData(selected_account_id)

            if index >= 0:
                self.m_account_selector.setCurrentIndex(index)

        self.m_account_selector.blockSignals(False)

        self._on_account_changed()

    def get_selected_account_id(self) -> Optional[int]:
        """Return the selected account's database identifier."""
        account_id = self.m_account_selector.currentData()

        return account_id if type(account_id) is int else None

    def _on_account_changed(self, *_args) -> None:
        """Reload positions and update controls after account selection."""
        account_id = self.get_selected_account_id()

        account = self.m_repository.get_trading_account(account_id) if account_id is not None else None

        can_create = self.m_service is not None and account is not None and account.is_active

        self.m_create_button.setEnabled(can_create)

        self.refresh_positions()

    def refresh_positions(self) -> None:
        """Display persisted positions for the selected account."""
        account_id = self.get_selected_account_id()

        positions = self.m_repository.get_positions(account_id=account_id) if account_id is not None else []

        self.m_table.setRowCount(len(positions))

        for row_index, position in enumerate(positions):
            values = [
                position.ticker,
                position.strategy,
                position.catalyst,
                str(position.position_id),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                item.setData(
                    Qt.UserRole,
                    position.position_id,
                )

                self.m_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.m_empty_label.setVisible(len(positions) == 0)
