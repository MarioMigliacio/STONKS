# =============================================================================
# File: research_page.py
# Purpose: Presents the historical research workspace and its visual regions.
# =============================================================================

from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stonks.models.historical_research_request import HistoricalResearchRequest
from stonks.models.historical_research_result import (
    HistoricalResearchResult,
    ResearchDataStatus,
)
from stonks.models.market_session import MarketSession
from stonks.models.research_interval import ResearchInterval


class ResearchPage(QWidget):
    """Present the Historical Research workspace.

    Attributes:
        m_status_label:
            Label describing the current research state.

        m_ticker_input:
            Input for the research ticker symbol.

        m_start_date:
            Inclusive start date for historical research.

        m_end_date:
            Inclusive end date, disabled for intraday intervals.

        m_end_date_label:
            Label accompanying the end-date control.

        m_session_combo:
            Selector for intraday market sessions.

        m_session_label:
            Label accompanying the market-session control.

        m_interval_combo:
            Selector for the display candle interval.

        m_analyze_button:
            Action button reserved for analysis requests.

        m_refresh_button:
            Action button reserved for explicit data refresh.

        m_chart_panel:
            Container reserved for historical candle visualization.

        m_metrics_panel:
            Container reserved for price-action metrics.

        m_running:
            Whether a research request is currently being processed.

        m_presentation_state:
            Current visual state of the research workspace.

        m_chart_message:
            Placeholder text for the chart region.

        m_metrics_message:
            Placeholder text for the metrics region.

    Signals:
        research_requested:
            Emitted with a validated HistoricalResearchRequest.
    """

    research_requested = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Construct the research workspace and configuration controls."""
        super().__init__(parent)
        self.setObjectName("researchWorkspace")
        self.m_running = False
        self.m_presentation_state = "ready"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)

        eyebrow = QLabel("STONKS / MARKET INTELLIGENCE")
        eyebrow.setObjectName("researchEyebrow")
        title_stack.addWidget(eyebrow)

        title = QLabel("Historical Research")
        title.setObjectName("researchTitle")
        title_stack.addWidget(title)

        subtitle = QLabel("Explore historical price action. Understand the movement.")
        subtitle.setObjectName("researchSubtitle")
        title_stack.addWidget(subtitle)
        header.addLayout(title_stack, 1)

        self.m_status_label = QLabel("SYSTEM READY")
        self.m_status_label.setObjectName("researchStatus")
        self.m_status_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.m_status_label)
        layout.addLayout(header)

        configuration = QFrame()
        configuration.setObjectName("researchPanel")
        configuration_layout = QVBoxLayout(configuration)
        configuration_layout.setContentsMargins(16, 14, 16, 14)
        configuration_layout.setSpacing(12)
        configuration_layout.addWidget(QLabel("Research Configuration"))

        controls = QGridLayout()
        controls.setHorizontalSpacing(12)
        controls.setVerticalSpacing(10)

        controls.addWidget(QLabel("Ticker"), 0, 0)
        self.m_ticker_input = QLineEdit()
        self.m_ticker_input.setObjectName("researchTickerInput")
        self.m_ticker_input.setPlaceholderText("e.g. NVDA")
        self.m_ticker_input.setMaxLength(16)
        controls.addWidget(self.m_ticker_input, 1, 0)

        controls.addWidget(QLabel("Start Date"), 0, 1)
        self.m_start_date = QDateEdit()
        self.m_start_date.setObjectName("researchStartDate")
        self.m_start_date.setCalendarPopup(True)
        self.m_start_date.setDisplayFormat("yyyy-MM-dd")
        self.m_start_date.setDate(QDate.currentDate())
        controls.addWidget(self.m_start_date, 1, 1)

        self.m_end_date_label = QLabel("End Date")
        controls.addWidget(self.m_end_date_label, 0, 2)
        self.m_end_date = QDateEdit()
        self.m_end_date.setObjectName("researchEndDate")
        self.m_end_date.setCalendarPopup(True)
        self.m_end_date.setDisplayFormat("yyyy-MM-dd")
        self.m_end_date.setDate(QDate.currentDate())
        controls.addWidget(self.m_end_date, 1, 2)

        self.m_session_label = QLabel("Market Session")
        controls.addWidget(self.m_session_label, 2, 0)
        self.m_session_combo = QComboBox()
        self.m_session_combo.setObjectName("researchSession")
        self.m_session_combo.addItem("All Sessions", None)
        self.m_session_combo.addItem("Pre-Market", MarketSession.PRE_MARKET)
        self.m_session_combo.addItem("Regular", MarketSession.REGULAR)
        self.m_session_combo.addItem("After-Hours", MarketSession.AFTER_HOURS)
        controls.addWidget(self.m_session_combo, 3, 0)

        controls.addWidget(QLabel("Display Interval"), 2, 1)
        self.m_interval_combo = QComboBox()
        self.m_interval_combo.setObjectName("researchInterval")
        interval_options = (
            ("1 Minute", ResearchInterval.ONE_MINUTE),
            ("5 Minutes", ResearchInterval.FIVE_MINUTES),
            ("10 Minutes", ResearchInterval.TEN_MINUTES),
            ("15 Minutes", ResearchInterval.FIFTEEN_MINUTES),
            ("30 Minutes", ResearchInterval.THIRTY_MINUTES),
            ("60 Minutes", ResearchInterval.SIXTY_MINUTES),
            ("Daily", ResearchInterval.DAILY),
            ("Weekly", ResearchInterval.WEEKLY),
            ("Monthly", ResearchInterval.MONTHLY),
            ("Quarterly", ResearchInterval.QUARTERLY),
        )
        for label, interval in interval_options:
            self.m_interval_combo.addItem(label, interval)
        controls.addWidget(self.m_interval_combo, 3, 1)
        configuration_layout.addLayout(controls)

        actions = QHBoxLayout()
        actions.addStretch()
        self.m_refresh_button = QPushButton("Refresh")
        self.m_refresh_button.setObjectName("researchRefreshButton")
        actions.addWidget(self.m_refresh_button)
        self.m_refresh_button.clicked.connect(lambda: self._request_research(force_refresh=True))
        self.m_analyze_button = QPushButton("Analyze")
        self.m_analyze_button.setObjectName("researchAnalyzeButton")
        actions.addWidget(self.m_analyze_button)
        self.m_analyze_button.clicked.connect(lambda: self._request_research(force_refresh=False))
        configuration_layout.addLayout(actions)

        self.m_interval_combo.currentIndexChanged.connect(self._update_interval_controls)
        self.m_start_date.dateChanged.connect(self._sync_intraday_date)
        self._update_interval_controls()
        layout.addWidget(configuration)

        self.m_chart_panel = QFrame()
        self.m_chart_panel.setObjectName("researchChartPanel")
        chart_layout = QVBoxLayout(self.m_chart_panel)
        self.m_chart_message = QLabel()
        self.m_chart_message.setObjectName("researchChartMessage")
        self.m_chart_message.setAlignment(Qt.AlignCenter)
        self.m_chart_message.setWordWrap(True)
        chart_layout.addWidget(self.m_chart_message)
        layout.addWidget(self.m_chart_panel, 1)

        self.m_metrics_panel = QFrame()
        self.m_metrics_panel.setObjectName("researchMetricsPanel")
        metrics_layout = QVBoxLayout(self.m_metrics_panel)
        self.m_metrics_message = QLabel()
        self.m_metrics_message.setObjectName("researchMetricsMessage")
        self.m_metrics_message.setWordWrap(True)
        metrics_layout.addWidget(self.m_metrics_message)
        layout.addWidget(self.m_metrics_panel)
        self.show_ready()

    def _is_intraday_interval(self) -> bool:
        """Return whether the selected interval uses minute candles."""
        return self.m_interval_combo.currentData() in {
            ResearchInterval.ONE_MINUTE,
            ResearchInterval.FIVE_MINUTES,
            ResearchInterval.TEN_MINUTES,
            ResearchInterval.FIFTEEN_MINUTES,
            ResearchInterval.THIRTY_MINUTES,
            ResearchInterval.SIXTY_MINUTES,
        }

    def _update_interval_controls(self) -> None:
        """Adapt date and session controls to the selected interval."""
        intraday = self._is_intraday_interval()
        self.m_end_date.setEnabled(not intraday)
        self.m_end_date_label.setEnabled(not intraday)
        self.m_session_combo.setEnabled(intraday)
        self.m_session_label.setEnabled(intraday)

        if intraday:
            self.m_end_date.setDate(self.m_start_date.date())
        else:
            self.m_session_combo.setCurrentIndex(0)

    def _sync_intraday_date(self) -> None:
        """Keep intraday research restricted to one trading date."""
        if self._is_intraday_interval():
            self.m_end_date.setDate(self.m_start_date.date())

    def _request_research(self, force_refresh: bool) -> None:
        """Validate controls and emit a research request without running it."""
        if self.m_running:
            return

        interval = self.m_interval_combo.currentData()
        start_date = self.m_start_date.date().toPython()
        end_date = start_date if self._is_intraday_interval() else self.m_end_date.date().toPython()
        session = self.m_session_combo.currentData() if self._is_intraday_interval() else None

        try:
            request = HistoricalResearchRequest(
                symbol=self.m_ticker_input.text(),
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                session=session,
                force_refresh=force_refresh,
            )
        except ValueError as error:
            self.set_status(f"Invalid research request: {error}")
            return

        self.show_loading()
        self.research_requested.emit(request)

    def set_running(self, running: bool) -> None:
        """Disable request controls while an external worker is active."""
        self.m_running = running
        for widget in (
            self.m_ticker_input,
            self.m_start_date,
            self.m_end_date,
            self.m_session_combo,
            self.m_interval_combo,
            self.m_analyze_button,
            self.m_refresh_button,
        ):
            widget.setEnabled(not running)

        if not running:
            self._update_interval_controls()

    def set_status(self, message: str) -> None:
        """Display validation or execution feedback without altering results."""
        self.m_status_label.setText(message)

    def _show_presentation(self, state: str, status: str, chart: str, metrics: str) -> None:
        """Update all presentation regions as one consistent state."""
        self.m_presentation_state = state
        self.set_status(status)
        self.m_chart_message.setText(chart)
        self.m_metrics_message.setText(metrics)

    def show_ready(self) -> None:
        """Present the initial workspace before research has been requested."""
        self.set_running(False)
        self._show_presentation(
            "ready",
            "SYSTEM READY",
            "Historical price visualization will appear here.",
            "Price Action  |  Volume  |  Source Data",
        )

    def show_loading(self) -> None:
        """Indicate that a request is pending external execution."""
        self.set_running(True)
        self._show_presentation(
            "loading",
            "RESEARCH PENDING",
            "Preparing historical research…",
            "Awaiting research results.",
        )

    def show_result(self, result: HistoricalResearchResult) -> None:
        """Present a research result without rendering a chart or detailed metrics."""
        if result.status == ResearchDataStatus.UNAVAILABLE:
            self.show_empty(result.message or "No historical data found.")
            return
        if result.status == ResearchDataStatus.ERROR:
            self.show_error(result.message or "Historical research failed.")
            return
        if result.status not in (
            ResearchDataStatus.AVAILABLE,
            ResearchDataStatus.PARTIAL,
        ):
            raise ValueError("Unsupported research result status.")

        self.set_running(False)
        state = "partial" if result.status == ResearchDataStatus.PARTIAL else "available"
        status = "PARTIAL DATA" if state == "partial" else "DATA AVAILABLE"
        source = result.data_source.value if result.data_source is not None else "unknown"
        chart = (
            f"{len(result.display_candles)} display candles ready for charting. Candlestick rendering arrives in #146."
        )
        metrics = (
            f"{len(result.source_candles)} source candles | "
            f"Source: {source} | "
            f"Incomplete periods: {result.incomplete_display_periods}"
        )
        if result.message:
            metrics += f" | {result.message}"
        self._show_presentation(state, status, chart, metrics)

    def show_empty(self, message: str = "No historical data found.") -> None:
        """Show an empty result without retaining stale chart information."""
        self.set_running(False)
        self._show_presentation("empty", "NO DATA", message, "No metrics available.")

    def show_error(self, message: str) -> None:
        """Show a research failure and allow another request."""
        self.set_running(False)
        self._show_presentation("error", "RESEARCH ERROR", message, "No metrics available.")
