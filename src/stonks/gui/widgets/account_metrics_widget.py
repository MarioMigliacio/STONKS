# =============================================================================
# File: account_metrics_widget.py
# Purpose: Display account financial metrics in reusable summary cards.
# =============================================================================

from decimal import Decimal

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from stonks.journal.analytics.account_metrics import AccountMetrics


class AccountMetricsWidget(QWidget):
    """Display book-value account metrics without estimating market equity.

    Attributes:
        m_cash_balance:
            Ledger-derived cash value.

        m_contributions:
            External deposits minus withdrawals.

        m_realized_pnl:
            Realized trading P&L net of standalone fees.

        m_equity:
            Equity measured at historical cost basis.
    """

    def __init__(self, parent=None) -> None:
        """Construct a grid of account metric cards."""
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        heading = QLabel("Account Performance")
        heading.setObjectName("metricsHeading")
        layout.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.m_cash_balance = self._add_card(grid, 0, 0, "Cash Balance")
        self.m_contributions = self._add_card(grid, 0, 1, "Net Contributions")
        self.m_realized_pnl = self._add_card(grid, 1, 0, "Net Realized P&L")
        self.m_equity = self._add_card(grid, 1, 1, "Equity at Cost Basis")
        layout.addLayout(grid)

        note = QLabel("Ledger values are not live brokerage balances or market valuations.")
        note.setObjectName("accountMetricsNote")
        note.setWordWrap(True)
        layout.addWidget(note)

    @staticmethod
    def _add_card(grid: QGridLayout, row: int, column: int, caption: str) -> QLabel:
        """Create a caption/value card matching the position details theme."""
        card = QFrame()
        card.setObjectName("metricCard")
        content = QVBoxLayout(card)
        label = QLabel(caption)
        label.setObjectName("metricCaption")
        value = QLabel("$0.00")
        value.setObjectName("metricValue")
        content.addWidget(label)
        content.addWidget(value)
        grid.addWidget(card, row, column)

        return value

    @staticmethod
    def _money(value: Decimal, signed: bool = False) -> str:
        """Format an exact decimal as currency for presentation."""
        if signed and value > 0:
            return f"+${value:,.2f}"

        if value < 0:
            return f"-${abs(value):,.2f}"

        return f"${value:,.2f}"

    def update_metrics(self, metrics: AccountMetrics) -> None:
        """Populate the cards from existing backend calculations."""
        self.m_cash_balance.setText(self._money(metrics.cash_balance))
        self.m_contributions.setText(self._money(metrics.net_contributions))
        self.m_realized_pnl.setText(self._money(metrics.net_realized_pnl, signed=True))
        self.m_equity.setText(self._money(metrics.equity_at_cost_basis))
        value = metrics.net_realized_pnl
        status = "profit" if value > 0 else "loss" if value < 0 else "neutral"
        self.m_realized_pnl.setProperty("performance", status)
        self.m_realized_pnl.style().unpolish(self.m_realized_pnl)
        self.m_realized_pnl.style().polish(self.m_realized_pnl)
