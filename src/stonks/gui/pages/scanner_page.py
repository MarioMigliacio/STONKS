# =============================================================================
# File: scanner_page.py
# Purpose: Presents scanner selection, execution controls, and market results.
# =============================================================================

from typing import Iterable, List, Tuple

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.gui.icons import get_icon
from stonks.gui.styles.scanner_theme import SCANNER_NEGATIVE_COLOR, SCANNER_POSITIVE_COLOR
from stonks.models.scanner_candidate import ScannerCandidate
from stonks.scanner.scanner_match_mode import ScannerMatchMode


class ScannerPage(QWidget):
    """Present scanner configuration and results without executing scans.

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

        m_running:
            Whether the scanner controller is currently active.

        m_matches_value:
            Summary label showing the last successful result count.

        m_active_value:
            Summary label showing the selected strategy count.

        m_state_value:
            Summary label showing the execution state.

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
        """Construct the styled scanner workspace.

        Args:
            strategies: Iterable of unique (strategy_id, display_name) pairs.
            parent: Optional parent widget.

        Raises:
            ValueError: If strategy identifiers are duplicated or empty.
        """
        super().__init__(parent)
        entries = list(strategies)
        identifiers = [identifier for identifier, _ in entries]

        if any(not identifier.strip() for identifier in identifiers):
            raise ValueError("Scanner strategy identifiers cannot be empty.")
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Scanner strategy identifiers must be unique.")

        self.setObjectName("scannerWorkspace")
        self.m_running = False
        self.m_strategy_checkboxes = {}
        self.m_last_result_count = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)
        title_stack.addWidget(self._label("STONKS / MARKET INTELLIGENCE", "scannerEyebrow"))
        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title_icon = QLabel()
        title_icon.setPixmap(get_icon("scan-search").pixmap(QSize(24, 24)))
        title_icon.setFixedSize(24, 24)

        title_row.addWidget(title_icon)
        title_row.addWidget(self._label("Market Scanner", "scannerTitle"))
        title_row.addStretch()

        title_stack.addLayout(title_row)
        title_stack.addWidget(self._label("Discover opportunities. Validate the signal.", "scannerSubtitle"))
        header.addLayout(title_stack, 1)
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        status_icon = QLabel()
        status_icon.setPixmap(get_icon("activity").pixmap(QSize(16, 16)))
        status_icon.setFixedSize(16, 16)

        self.m_system_badge = self._label("SYSTEM READY", "scannerKicker")
        self.m_system_badge.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_row.addWidget(status_icon)
        status_row.addWidget(self.m_system_badge)

        header.addLayout(status_row)
        header.setSpacing(16)
        layout.addLayout(header)

        configuration = self._panel("scannerPanel")
        configuration_layout = QVBoxLayout(configuration)
        configuration_layout.setContentsMargins(16, 14, 16, 14)
        configuration_layout.setSpacing(12)
        section_header = QHBoxLayout()
        section_header.setSpacing(8)
        configuration_icon = QLabel()
        configuration_icon.setPixmap(get_icon("sliders-horizontal").pixmap(QSize(18, 18)))
        configuration_icon.setFixedSize(18, 18)

        section_header.addWidget(configuration_icon)
        section_header.addWidget(self._label("Scanner Configuration", "scannerSectionTitle"))
        section_header.addStretch()
        section_header.addWidget(self._label(f"{len(entries)} STRATEGY AVAILABLE", "scannerHint"))
        configuration_layout.addLayout(section_header)

        strategy_card = self._panel("scannerStrategyCard")
        strategy_layout = QVBoxLayout(strategy_card)
        strategy_layout.setContentsMargins(14, 12, 14, 12)

        for identifier, display_name in entries:
            checkbox = QCheckBox(display_name)
            checkbox.setObjectName("scannerStrategyCheck")
            checkbox.toggled.connect(self._update_run_enabled)
            checkbox.toggled.connect(self._refresh_strategy_card)
            strategy_layout.addWidget(checkbox)
            self.m_strategy_checkboxes[identifier] = checkbox
        configuration_layout.addWidget(strategy_card)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(self._label("MATCH MODE", "scannerHint"))
        self.m_match_mode = QComboBox()
        self.m_match_mode.setObjectName("scannerMatchMode")
        self.m_match_mode.addItem("ANY — at least one", ScannerMatchMode.ANY)
        self.m_match_mode.addItem("ALL — every strategy", ScannerMatchMode.ALL)

        self.m_match_mode.hide()
        self.m_mode_buttons = QButtonGroup(self)
        self.m_mode_buttons.setExclusive(True)

        for index, label in enumerate(("ANY", "ALL")):
            button = QPushButton(label)
            button.setObjectName("scannerModeButton")
            button.setCheckable(True)
            button.setProperty("modeIndex", index)
            self.m_mode_buttons.addButton(button, index)
            controls.addWidget(button)
            button.clicked.connect(
                lambda checked=False, selected_index=index: self.m_match_mode.setCurrentIndex(selected_index)
            )

        self.m_mode_buttons.button(0).setChecked(True)
        self.m_match_mode.currentIndexChanged.connect(self._sync_match_buttons)
        controls.addStretch()
        self.m_cancel_button = QPushButton("Cancel")
        self.m_cancel_button.setIcon(get_icon("square"))
        self.m_cancel_button.setObjectName("scannerCancelButton")
        self.m_cancel_button.setEnabled(False)
        self.m_cancel_button.clicked.connect(self.cancel_requested.emit)
        controls.addWidget(self.m_cancel_button)
        self.m_run_button = QPushButton("Run Scanner")
        self.m_run_button.setIcon(get_icon("play"))
        self.m_run_button.setObjectName("scannerRunButton")
        self.m_run_button.clicked.connect(self._request_run)
        controls.addWidget(self.m_run_button)
        configuration_layout.addLayout(controls)
        layout.addWidget(configuration)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        state_card, self.m_state_value = self._metric("EXECUTION STATUS", "Ready", "scannerStateValue")
        matches_card, self.m_matches_value = self._metric("MATCHES FOUND", "—")
        active_card, self.m_active_value = self._metric("ACTIVE STRATEGIES", "00")

        for card in (state_card, matches_card, active_card):
            metrics.addWidget(card, 1)

        layout.addLayout(metrics)

        results_panel = self._panel("scannerPanel")
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(14, 14, 14, 12)
        results_layout.setSpacing(10)
        results_header = QHBoxLayout()
        results_header.addWidget(self._label("Scanner Results", "scannerSectionTitle"))
        results_header.addStretch()
        results_header.addWidget(self._label("MARKET DATA", "scannerHint"))
        results_layout.addLayout(results_header)

        self.m_results_table = QTableWidget(0, len(self.COLUMNS))
        self.m_results_table.setObjectName("scannerResults")
        self.m_results_table.setHorizontalHeaderLabels(self.COLUMNS)
        self.m_results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.m_results_table.setAlternatingRowColors(True)
        self.m_results_table.setShowGrid(False)
        self.m_results_table.verticalHeader().setVisible(False)
        self.m_results_table.verticalHeader().setDefaultSectionSize(32)

        # Avoid truncating float values and the final header at the default size.
        # Keep full-width data available through horizontal scrolling.

        header_view = self.m_results_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Interactive)

        for column, width in enumerate((78, 98, 118, 100, 94, 72, 132, 138)):
            self.m_results_table.setColumnWidth(column, width)

        header_view.setMinimumSectionSize(64)
        header_view.setSectionResizeMode(
            len(self.COLUMNS) - 1,
            QHeaderView.Stretch,
        )

        self.m_results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.m_results_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        results_layout.addWidget(self.m_results_table, 1)
        self.m_status_label = self._label("Ready", "scannerStatus")
        results_layout.addWidget(self.m_status_label)
        layout.addWidget(results_panel, 1)
        self._update_run_enabled()
        self._refresh_strategy_card()

    @staticmethod
    def _label(text: str, object_name: str) -> QLabel:
        """Build a text label with a scoped style identifier."""
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    @staticmethod
    def _panel(object_name: str) -> QFrame:
        """Build a styled, reusable visual container."""
        panel = QFrame()
        panel.setObjectName(object_name)
        return panel

    def _metric(self, caption: str, value: str, value_style: str = "scannerMetricValue") -> Tuple[QFrame, QLabel]:
        """Build a summary card and return its editable value label."""
        card = self._panel("scannerMetric")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(6)
        card_layout.addWidget(self._label(caption, "scannerMetricCaption"))
        value_label = self._label(value, value_style)
        card_layout.addWidget(value_label)
        return card, value_label

    def _sync_match_buttons(self, index: int) -> None:
        """Keep the visible segmented buttons in sync with the match-mode model."""
        for button_id in (0, 1):
            button = self.m_mode_buttons.button(button_id)
            button.setChecked(button_id == index)

    def _refresh_strategy_card(self) -> None:
        """Refresh selected-card appearance using the centralized theme."""
        for checkbox in self.m_strategy_checkboxes.values():
            checkbox.setProperty("selected", checkbox.isChecked())
            checkbox.style().unpolish(checkbox)
            checkbox.style().polish(checkbox)

    def selected_strategy_ids(self) -> List[str]:
        """Return selected strategy identifiers in display order."""
        return [identifier for identifier, checkbox in self.m_strategy_checkboxes.items() if checkbox.isChecked()]

    def _update_run_enabled(self) -> None:
        """Enable Run only when idle and at least one strategy is selected."""
        self.m_run_button.setEnabled(not self.m_running and bool(self.selected_strategy_ids()))
        self.m_active_value.setText(f"{len(self.selected_strategy_ids()):02d}")

    def _request_run(self) -> None:
        """Emit selected configuration without executing work on the GUI thread."""
        identifiers = self.selected_strategy_ids()

        if identifiers and not self.m_running:
            self.run_requested.emit(identifiers, self.m_match_mode.currentData())

    def set_running(self, running: bool) -> None:
        """Update controls while preserving the final outcome status when idle.

        Args:
            running: True while the scanner thread is active.
        """
        self.m_running = running

        for checkbox in self.m_strategy_checkboxes.values():
            checkbox.setEnabled(not running)
        self.m_match_mode.setEnabled(not running)

        for button in self.m_mode_buttons.buttons():
            button.setEnabled(not running)

        self.m_cancel_button.setEnabled(running)
        self._update_run_enabled()

        if running:
            self.set_status("Scanning…")

    def set_status(self, message: str) -> None:
        """Display execution feedback and synchronize the status summary.

        Args:
            message: Human-readable status.
        """
        self.m_status_label.setText(message)
        normalized = message.lower()

        if "cancel" in normalized:
            state, badge = "Cancelled", "CANCELLED"
        elif "fail" in normalized or "unable" in normalized or "error" in normalized:
            state, badge = "Failed", "SCAN ERROR"
        elif "scanning" in normalized:
            state, badge = "Scanning", "SCANNING"
        elif "complete" in normalized:
            state, badge = "Complete", "SCAN COMPLETE"
        else:
            state, badge = "Ready", "SYSTEM READY"

        self.m_state_value.setText(state)
        self.m_system_badge.setText(badge)

    def set_results(self, candidates: List[ScannerCandidate]) -> None:
        """Replace displayed results with scanner candidates.

        Args:
            candidates:
                Market candidates returned by the scanner.
        """
        self.m_last_result_count = len(candidates)
        self.m_matches_value.setText(str(self.m_last_result_count))
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
                item = QTableWidgetItem(value)

                if column == 0:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                elif column in (3, 4):
                    change = quote.change_percent if column == 3 else quote.gap_percent
                    if change > 0:
                        item.setForeground(QColor(SCANNER_POSITIVE_COLOR))
                    elif change < 0:
                        item.setForeground(QColor(SCANNER_NEGATIVE_COLOR))
                if column > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                item.setToolTip(value)
                self.m_results_table.setItem(row, column, item)
