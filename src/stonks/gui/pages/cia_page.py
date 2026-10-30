# =============================================================================
# File: cia_page.py
# Purpose: Presents the CIA Mission Brief without executing network requests.
# =============================================================================

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from stonks.cia.cia_analysis_result import CiaAnalysisResult
from stonks.gui.widgets.cia_article_dossier import CiaArticleDossier
from stonks.gui.widgets.cia_intelligence_sources import CiaIntelligenceSources
from stonks.models.news_article import NewsArticle


class CiaPage(QWidget):
    """Present CIA analysis and request background execution.

    Attributes:
        m_ticker_input:
            Input for ticker searches.

        m_analyze_button:
            Button requesting analysis.

        m_status_label:
            Execution feedback label.

        m_metrics:
            Named report metric labels.

        m_last_result:
            Most recent successful result.

        m_sources:
            Supporting intelligence widget.

        m_view_stack:
            Stacked workspace containing the Mission Brief and article dossier.

        m_brief_scroll:
            Scrollable container preserving the Mission Brief's position.

        m_dossier:
            Article dossier displaying the selected intelligence source.

        m_running:
            Whether a request is in progress.
    """

    analysis_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Construct the Mission Brief workspace."""
        super().__init__(parent)
        self.setObjectName("ciaWorkspace")
        self.m_last_result: Optional[CiaAnalysisResult] = None
        self.m_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        eyebrow = QLabel("STONKS / CATALYST INTELLIGENCE ANALYSIS")
        eyebrow.setObjectName("ciaEyebrow")
        layout.addWidget(eyebrow)
        title = QLabel("Mission Brief")
        title.setObjectName("ciaTitle")
        layout.addWidget(title)
        subtitle = QLabel("Investigate catalysts. Validate the intelligence.")
        subtitle.setObjectName("ciaSubtitle")
        layout.addWidget(subtitle)

        controls = QHBoxLayout()
        self.m_ticker_input = QLineEdit()
        self.m_ticker_input.setObjectName("ciaTickerInput")
        self.m_ticker_input.setPlaceholderText("Ticker symbol (e.g. AMD)")
        self.m_ticker_input.setMaxLength(16)
        self.m_ticker_input.returnPressed.connect(self._request_analysis)
        controls.addWidget(self.m_ticker_input, 1)
        self.m_analyze_button = QPushButton("Analyze Ticker")
        self.m_analyze_button.setObjectName("ciaAnalyzeButton")
        self.m_analyze_button.clicked.connect(self._request_analysis)
        controls.addWidget(self.m_analyze_button)
        layout.addLayout(controls)

        self.m_status_label = QLabel("Enter a ticker to request a briefing.")
        self.m_status_label.setObjectName("ciaStatus")
        self.m_status_label.setWordWrap(True)
        layout.addWidget(self.m_status_label)

        self.m_view_stack = QStackedWidget()
        self.m_view_stack.setObjectName("ciaViewStack")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("ciaBriefScroll")
        self.m_brief_container = QWidget()
        self.m_brief_container.setObjectName("ciaBriefContainer")
        brief = QVBoxLayout(self.m_brief_container)
        brief.setSpacing(16)
        self.m_target = QLabel("TARGET: —")
        self.m_target.setObjectName("ciaTarget")
        brief.addWidget(self.m_target)
        self.m_mission_status = QLabel("AWAITING INTELLIGENCE")
        self.m_mission_status.setObjectName("ciaMissionStatus")
        brief.addWidget(self.m_mission_status)

        metrics = QGridLayout()
        self.m_metrics = {}

        for index, (key, caption) in enumerate(
            (
                ("strength", "CATALYST STRENGTH"),
                ("freshness", "FRESHNESS"),
                ("sentiment", "SENTIMENT"),
                ("confidence", "CONFIDENCE"),
                ("articles", "ARTICLES REVIEWED"),
                ("duplicates", "DUPLICATES REMOVED"),
            )
        ):
            panel = QFrame()
            panel.setObjectName("ciaMetricPanel")
            panel_layout = QVBoxLayout(panel)
            label = QLabel(caption)
            label.setObjectName("ciaMetricCaption")
            value = QLabel("—")
            value.setObjectName("ciaMetricValue")
            value.setWordWrap(True)
            panel_layout.addWidget(label)
            panel_layout.addWidget(value)
            metrics.addWidget(panel, index // 3, index % 3)
            self.m_metrics[key] = value

        brief.addLayout(metrics)
        self.m_current = self._section(brief, "CURRENT INTELLIGENCE")
        self.m_historical = self._section(brief, "HISTORICAL CONTEXT")
        self.m_summary = self._section(brief, "INTELLIGENCE SUMMARY")
        self.m_sources = CiaIntelligenceSources(self.m_brief_container)
        brief.addWidget(self.m_sources)
        brief.addStretch()

        scroll.setWidget(self.m_brief_container)
        self.m_brief_scroll = scroll
        self.m_view_stack.addWidget(self.m_brief_scroll)

        self.m_dossier = CiaArticleDossier(self)
        self.m_view_stack.addWidget(self.m_dossier)
        self.m_dossier.back_requested.connect(self._show_briefing)
        self.m_sources.article_activated.connect(self._show_dossier)

        layout.addWidget(self.m_view_stack, 1)
        self.m_view_stack.setCurrentWidget(self.m_brief_scroll)
        self.m_brief_container.hide()

    @staticmethod
    def _section(layout: QVBoxLayout, title: str) -> QLabel:
        """Append a titled section and return its content label."""
        heading = QLabel(title)
        heading.setObjectName("ciaSectionTitle")
        layout.addWidget(heading)
        content = QLabel("—")
        content.setObjectName("ciaSectionBody")
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(content)
        return content

    def _request_analysis(self) -> None:
        """Emit the normalized ticker when a request is valid."""
        if self.m_running:
            return

        ticker = self.m_ticker_input.text().strip().upper()

        if not ticker:
            self.set_status("Enter a ticker symbol before analyzing.")
            return

        self.analysis_requested.emit(ticker)

    def set_running(self, running: bool) -> None:
        """Disable repeated requests while analysis is running."""
        self.m_running = running
        self.m_ticker_input.setEnabled(not running)
        self.m_analyze_button.setEnabled(not running)

        if running:
            self.set_status("Retrieving news and analyzing catalysts…")

    def set_status(self, message: str) -> None:
        """Update status without discarding the previous report."""
        self.m_status_label.setText(message)

    def set_result(self, result: CiaAnalysisResult) -> None:
        """Display the successful report and retain supporting articles."""
        self.m_last_result = result
        report = result.report
        self.m_target.setText(f"TARGET: {report.ticker}")

        if report.has_breaking_news:
            status = "BREAKING CATALYST DETECTED"
        elif report.categories:
            status = "ACTIVE CATALYST DETECTED"
        else:
            status = "NO ACTIVE CATALYST"

        self.m_mission_status.setText(status)
        self.m_metrics["strength"].setText(report.catalyst_strength.value)
        self.m_metrics["freshness"].setText(report.freshness.value)
        self.m_metrics["sentiment"].setText(f"{report.overall_sentiment} ({report.average_sentiment:+.2f})")
        self.m_metrics["confidence"].setText(f"{report.confidence:.0%}")
        self.m_metrics["articles"].setText(f"{report.unique_article_count} / {report.original_article_count}")
        self.m_metrics["duplicates"].setText(str(report.duplicate_articles_removed))
        self.m_current.setText("\n".join(category.value for category in report.categories) or "None")
        self.m_historical.setText("\n".join(category.value for category in report.historical_categories) or "None")
        self.m_summary.setText(report.summary)
        self.m_sources.set_articles(result.articles)
        self.m_brief_container.show()
        self.m_view_stack.setCurrentWidget(self.m_brief_scroll)
        self.set_status(
            f"Briefing complete for {report.ticker}. {report.unique_article_count} unique article(s) analyzed."
        )

    def _show_dossier(self, article: NewsArticle) -> None:
        """Open the selected normalized article without requesting news again."""
        self.m_dossier.set_article(article)
        self.m_view_stack.setCurrentWidget(self.m_dossier)
        self.m_dossier.m_back_button.setFocus()

    def _show_briefing(self) -> None:
        """Restore the existing briefing and selected source row."""
        self.m_view_stack.setCurrentWidget(self.m_brief_scroll)
        self.m_sources.m_table.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Allow Backspace or Escape to return from the dossier."""
        if self.m_view_stack.currentWidget() is self.m_dossier and event.key() in (Qt.Key_Backspace, Qt.Key_Escape):
            self._show_briefing()
            event.accept()
            return
        super().keyPressEvent(event)
