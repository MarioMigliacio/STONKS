# =============================================================================
# File: scanner_page.py
# Purpose: Presents scanner selection, execution controls, and market results.
# =============================================================================

from typing import Iterable, List, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_match_mode import ScannerMatchMode


class ScannerPage(QWidget):
    """
    Present scanner configuration and results without executing scans.

    Attributes:
        m_strategy_checkboxes:
            Mapping of strategy IDs to selection checkboxes.

        m_match_mode:
            Selector for ANY and ALL matching.

        m_run_button:
            Button requesting a scanner run.

        m_cancel_button:
            Button requesting cooperative cancellation.

        m_status_label:
            Text describing current execution state.

        m_results_table:
            Read-only table of matching scanner candidates.

    Signals:
        run_requested:
            Emitted with selected strategy IDs and match mode.

        cancel_requested:
            Emitted when the user requests cancellation.
    """

    run_requested = Signal(object, object)
    cancel_requested = Signal()

    COLUMNS = (
        "Ticker",
        "Price",
        "Volume",
        "Change %",
        "Gap %",
        "RVOL",
        "Float",
        "Float Turnover",
    )

    def __init__(
        self,
        strategies: Iterable[Tuple[str, str]],
        parent: QWidget = None,
    ) -> None:
        """
        Construct the scanner workspace.

        Args:
            strategies:
                Iterable of unique (strategy_id, display_name) pairs.
            parent:
                Optional parent widget.

        Raises:
            ValueError:
                If strategy identifiers are duplicated or empty.
        """
        super().__init__(parent)
        entries = list(strategies)
        identifiers = [identifier for identifier, _ in entries]
        if any(not identifier.strip() for identifier in identifiers):
            raise ValueError("Scanner strategy identifiers cannot be empty.")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Scanner strategy identifiers must be unique.")

        self.m_strategy_checkboxes = {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Market Scanner"))

        strategy_group = QGroupBox("Scanner strategies")
        strategy_layout = QVBoxLayout(strategy_group)
        for identifier, display_name in entries:
            checkbox = QCheckBox(display_name)
            strategy_layout.addWidget(checkbox)
            checkbox.toggled.connect(self._update_run_enabled)
            self.m_strategy_checkboxes[identifier] = checkbox
        layout.addWidget(strategy_group)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Match mode"))
        self.m_match_mode = QComboBox()
        self.m_match_mode.addItem("ANY — match at least one", ScannerMatchMode.ANY)
        self.m_match_mode.addItem("ALL — match every selected strategy", ScannerMatchMode.ALL)
        controls.addWidget(self.m_match_mode)

        self.m_run_button = QPushButton("Run Scan")
        self.m_run_button.clicked.connect(self._request_run)
        controls.addWidget(self.m_run_button)

        self.m_cancel_button = QPushButton("Cancel")
        self.m_cancel_button.setEnabled(False)
        self.m_cancel_button.clicked.connect(self.cancel_requested.emit)
        controls.addWidget(self.m_cancel_button)
        layout.addLayout(controls)

        self.m_status_label = QLabel("Ready")
        layout.addWidget(self.m_status_label)

        self.m_results_table = QTableWidget(0, len(self.COLUMNS))
        self.m_results_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.m_results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.m_results_table)
        self.m_running = False
        self._update_run_enabled()

    def selected_strategy_ids(self) -> List[str]:
        """
        Return selected strategy identifiers in display order.

        Returns:
            Ordered list of checked strategy identifiers.
        """
        return [identifier for identifier, checkbox in self.m_strategy_checkboxes.items() if checkbox.isChecked()]

    def _update_run_enabled(self) -> None:
        """Allow starting only when idle and a strategy is selected."""
        self.m_run_button.setEnabled(not self.m_running and bool(self.selected_strategy_ids()))

    def _request_run(self) -> None:
        """Emit the selected scan configuration without starting a worker."""
        identifiers = self.selected_strategy_ids()
        if identifiers and not self.m_running:
            self.run_requested.emit(
                identifiers,
                self.m_match_mode.currentData(),
            )

    def set_running(self, running: bool) -> None:
        """
        Update controls to reflect scanner execution state.

        Args:
            running:
                True while a scanner thread is active.
        """
        self.m_running = running
        for checkbox in self.m_strategy_checkboxes.values():
            checkbox.setEnabled(not running)
        self.m_match_mode.setEnabled(not running)
        self.m_cancel_button.setEnabled(running)
        self._update_run_enabled()
        self.m_status_label.setText("Scanning…" if running else "Ready")

    def set_status(self, message: str) -> None:
        """
        Display a scanner status message.

        Args:
            message:
                Human-readable status.
        """
        self.m_status_label.setText(message)

    def set_results(self, candidates: List[ScannerCandidate]) -> None:
        """
        Replace displayed results with scanner candidates.

        Args:
            candidates:
                Market candidates returned by the scanner.
        """
        self.m_results_table.setRowCount(len(candidates))
        for row, candidate in enumerate(candidates):
            quote = candidate.quote_data
            float_value = f"{candidate.float_data.float_shares:,.0f}" if candidate.float_data is not None else "—"
            turnover = f"{candidate.float_turnover:.2%}" if candidate.float_turnover is not None else "—"
            values = (
                quote.symbol,
                f"${quote.price:,.2f}",
                f"{quote.volume:,}",
                f"{quote.change_percent:+.2f}%",
                f"{quote.gap_percent:+.2f}%",
                f"{quote.relative_volume:.2f}",
                float_value,
                turnover,
            )
            for column, value in enumerate(values):
                self.m_results_table.setItem(row, column, QTableWidgetItem(value))
