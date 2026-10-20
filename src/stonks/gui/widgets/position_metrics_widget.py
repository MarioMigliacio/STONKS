# =============================================================================
# File: position_metrics_widget.py
# Purpose: Displays journal position performance in summary cards.
# =============================================================================

from decimal import Decimal
from typing import Optional

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from stonks.journal.analytics.position_metrics import PositionMetrics


class PositionMetricsWidget(QWidget):
    """
    Display calculated position performance using summary cards.

    Accounting calculations remain in the analytics layer.
    This widget is responsible only for formatting and presentation.

    Attributes:
        m_status:
            Badge displaying the position lifecycle status.

        m_open_shares:
            Label displaying shares currently held.

        m_average_entry:
            Label displaying historical weighted-average buy price.

        m_realized_pnl:
            Label displaying realized profit or loss after fees.

        m_realized_return:
            Label displaying realized return on sold shares.

        m_cost_basis:
            Label displaying remaining cost basis.
    """

    def __init__(self, parent=None) -> None:
        """Initialize the position performance cards."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construct the dashboard-style metric layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()

        heading = QLabel("Position Performance")
        heading.setObjectName("metricsHeading")

        self.m_status = QLabel("DRAFT")
        self.m_status.setObjectName("positionStatusBadge")

        header.addWidget(heading)
        header.addStretch()
        header.addWidget(self.m_status)

        layout.addLayout(header)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.m_open_shares = self._add_metric(grid, 0, 0, "Remaining Shares")

        self.m_average_entry = self._add_metric(grid, 0, 1, "Avg Buy Price")

        self.m_realized_pnl = self._add_metric(grid, 1, 0, "Realized P&L", "After fees")

        self.m_realized_return = self._add_metric(grid, 1, 1, "Realized Return", "On shares sold")

        layout.addLayout(grid)

        cost_basis_frame = QFrame()
        cost_basis_frame.setObjectName("metricFooter")

        cost_basis_layout = QHBoxLayout(cost_basis_frame)

        cost_basis_caption = QLabel("Remaining Cost Basis")
        cost_basis_caption.setObjectName("metricCaption")

        self.m_cost_basis = QLabel("$0.00")
        self.m_cost_basis.setObjectName("metricFooterValue")

        cost_basis_layout.addWidget(cost_basis_caption)
        cost_basis_layout.addStretch()
        cost_basis_layout.addWidget(self.m_cost_basis)

        layout.addWidget(cost_basis_frame)

    @staticmethod
    def _add_metric(
        grid: QGridLayout,
        row: int,
        column: int,
        caption: str,
        description: str = "",
    ) -> QLabel:
        """
        Add a styled metric card to the performance grid.

        Args:
            grid:
                Parent grid layout.

            row:
                Destination grid row.

            column:
                Destination grid column.

            caption:
                Name of the metric.

            description:
                Optional clarification shown beneath its value.

        Returns:
            QLabel:
                Value label updated when metrics are refreshed.
        """
        card = QFrame()
        card.setObjectName("metricCard")

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")

        value_label = QLabel("—")
        value_label.setObjectName("metricValue")

        layout.addWidget(caption_label)
        layout.addWidget(value_label)

        if description:
            description_label = QLabel(description)
            description_label.setObjectName("metricDescription")
            layout.addWidget(description_label)

        grid.addWidget(card, row, column)

        return value_label

    @staticmethod
    def _format_money(
        value: Decimal,
        signed: bool = False,
    ) -> str:
        """Format a financial amount with a currency symbol."""
        if signed:
            if value > 0:
                return f"+${value:,.2f}"

            if value < 0:
                return f"-${abs(value):,.2f}"

        return f"${value:,.2f}"

    @staticmethod
    def _format_percentage(
        value: Optional[Decimal],
    ) -> str:
        """Format an optional signed percentage."""
        if value is None:
            return "—"

        return f"{value:+,.2f}%"

    @staticmethod
    def _set_performance_style(
        label: QLabel,
        value: Decimal,
    ) -> None:
        """Apply a semantic profit, loss, or neutral style."""
        if value > 0:
            performance = "profit"
        elif value < 0:
            performance = "loss"
        else:
            performance = "neutral"

        label.setProperty("performance", performance)

        style = label.style()
        style.unpolish(label)
        style.polish(label)
        label.update()

    def update_metrics(
        self,
        metrics: PositionMetrics,
    ) -> None:
        """
        Refresh all displayed performance metrics.

        Args:
            metrics:
                Calculated position analytics.
        """
        self.m_status.setText(metrics.status.value)
        self.m_status.setProperty(
            "status",
            metrics.status.value,
        )

        status_style = self.m_status.style()
        status_style.unpolish(self.m_status)
        status_style.polish(self.m_status)

        self.m_open_shares.setText(format(metrics.open_shares, "f"))

        average_buy = metrics.average_buy_price

        self.m_average_entry.setText(self._format_money(average_buy) if average_buy is not None else "—")

        self.m_cost_basis.setText(self._format_money(metrics.remaining_cost_basis))

        self.m_realized_pnl.setText(self._format_money(metrics.realized_pnl, signed=True))

        self._set_performance_style(
            self.m_realized_pnl,
            metrics.realized_pnl,
        )

        self.m_realized_return.setText(self._format_percentage(metrics.realized_return_pct))

        if metrics.realized_return_pct is not None:
            self._set_performance_style(
                self.m_realized_return,
                metrics.realized_return_pct,
            )
        else:
            self.m_realized_return.setProperty("performance", "neutral")

            style = self.m_realized_return.style()
            style.unpolish(self.m_realized_return)
            style.polish(self.m_realized_return)
