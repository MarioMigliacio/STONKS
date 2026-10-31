# =============================================================================
# File: cia_page.py
# Purpose: Presents the CIA Mission Brief without executing network requests.
# =============================================================================

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
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
from stonks.gui.icons import get_icon
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

        m_system_badge:
            Styled CIA execution-state indicator in the workspace header.

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

        header = QHBoxLayout()
        title_stack = QVBoxLayout()
        title_stack.setSpacing(3)
        eyebrow = QLabel("STONKS / CATALYST INTELLIGENCE ANALYSIS")
        eyebrow.setObjectName("ciaEyebrow")
        title_stack.addWidget(eyebrow)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_icon = QLabel()
        title_icon.setObjectName("ciaTitleIcon")
        title_icon.setPixmap(get_icon("radar").pixmap(QSize(24, 24)))
        title_icon.setFixedSize(24, 24)
        title_row.addWidget(title_icon)
        title = QLabel("Mission Brief")
        title.setObjectName("ciaTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        title_stack.addLayout(title_row)

        subtitle = QLabel("Investigate catalysts. Validate the intelligence.")
        subtitle.setObjectName("ciaSubtitle")
        title_stack.addWidget(subtitle)
        header.addLayout(title_stack, 1)

        self.m_system_badge = QLabel("SYSTEM READY")
        self.m_system_badge.setObjectName("ciaKicker")
        self.m_system_badge.setProperty("state", "ready")
        self.m_system_badge.setAlignment(Qt.AlignCenter)
        header.addWidget(self.m_system_badge, 0, Qt.AlignVCenter)
        layout.addLayout(header)

        search_panel = QFrame()
        search_panel.setObjectName("ciaSearchPanel")
        search_layout = QVBoxLayout(search_panel)
        search_layout.setContentsMargins(16, 14, 16, 14)
        search_layout.setSpacing(10)
        search_header = QHBoxLayout()
        search_header.setSpacing(8)

        search_icon = QLabel()
        search_icon.setPixmap(get_icon("file-search").pixmap(QSize(18, 18)))
        search_icon.setFixedSize(18, 18)

        search_caption = QLabel("Intelligence Target")
        search_caption.setObjectName("ciaSearchCaption")

        search_header.addWidget(search_icon)
        search_header.addWidget(search_caption)
        search_header.addStretch()

        search_layout.addLayout(search_header)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.m_ticker_input = QLineEdit()
        self.m_ticker_input.setObjectName("ciaTickerInput")
        self.m_ticker_input.setPlaceholderText("Ticker symbol (e.g. AMD)")
        self.m_ticker_input.setMaxLength(16)
        self.m_ticker_input.returnPressed.connect(self._request_analysis)
        controls.addWidget(self.m_ticker_input, 1)

        self.m_analyze_button = QPushButton("Analyze Ticker")
        self.m_analyze_button.setObjectName("ciaAnalyzeButton")
        self.m_analyze_button.setIcon(get_icon("search-check"))
        self.m_analyze_button.setIconSize(QSize(17, 17))
        self.m_analyze_button.clicked.connect(self._request_analysis)
        controls.addWidget(self.m_analyze_button)
        search_layout.addLayout(controls)
        layout.addWidget(search_panel)

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

        mission_banner = QFrame()
        mission_banner.setObjectName("ciaMissionBanner")
        mission_row = QHBoxLayout(mission_banner)
        mission_row.setContentsMargins(16, 12, 16, 12)
        mission_row.setSpacing(12)

        self.m_target = QLabel("TARGET: —")
        self.m_target.setObjectName("ciaTarget")
        mission_row.addWidget(self.m_target, 1)

        self.m_mission_status = QLabel("AWAITING INTELLIGENCE")
        self.m_mission_status.setObjectName("ciaMissionStatus")
        self.m_mission_status.setProperty("catalyst", "none")
        mission_row.addWidget(self.m_mission_status)
        brief.addWidget(mission_banner)

        metrics = QGridLayout()
        metrics.setSpacing(12)

        for column in range(3):
            metrics.setColumnStretch(column, 1)

        self.m_metrics = {}

        metric_icons = {
            "strength": "gauge",
            "freshness": "clock-3",
            "sentiment": "activity",
            "confidence": "shield-alert",
            "articles": "newspaper",
            "duplicates": "layers",
        }

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
            panel_layout.setContentsMargins(15, 12, 15, 12)
            panel_layout.setSpacing(8)
            label = QLabel(caption)
            label.setObjectName("ciaMetricCaption")
            value = QLabel("—")
            value.setObjectName("ciaMetricValue")
            value.setProperty("signal", "neutral")
            value.setWordWrap(True)

            caption_row = QHBoxLayout()
            caption_row.setSpacing(8)
            metric_icon = QLabel()
            metric_icon.setPixmap(get_icon(metric_icons[key]).pixmap(QSize(16, 16)))
            metric_icon.setFixedSize(16, 16)
            caption_row.addWidget(metric_icon)
            caption_row.addWidget(label, 1)
            panel_layout.addLayout(caption_row)
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
        self.m_brief_scroll.hide()

    @staticmethod
    def _section(layout: QVBoxLayout, title: str) -> QLabel:
        """Append a styled intelligence section and return its content label."""
        panel = QFrame()
        panel.setObjectName("ciaIntelligenceSection")
        section_layout = QVBoxLayout(panel)
        section_layout.setContentsMargins(16, 14, 16, 14)
        section_layout.setSpacing(9)

        section_icons = {
            "CURRENT INTELLIGENCE": "shield-alert",
            "HISTORICAL CONTEXT": "rotate-ccw-clock",
            "INTELLIGENCE SUMMARY": "file-text",
        }
        heading_row = QHBoxLayout()
        heading_row.setSpacing(8)
        section_icon = QLabel()
        section_icon.setPixmap(get_icon(section_icons[title]).pixmap(QSize(17, 17)))
        section_icon.setFixedSize(17, 17)
        heading_row.addWidget(section_icon)

        heading = QLabel(title.title())
        heading.setObjectName("ciaSectionTitle")
        heading_row.addWidget(heading)
        heading_row.addStretch()
        section_layout.addLayout(heading_row)

        content = QLabel("—")
        content.setObjectName("ciaSectionBody")
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        section_layout.addWidget(content)
        layout.addWidget(panel)
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
            self._set_badge("ANALYZING", "running")

    def set_status(self, message: str) -> None:
        """Update status without discarding the previous report."""
        self.m_status_label.setText(message)
        normalized = message.lower()

        if "fail" in normalized or "unable" in normalized or "error" in normalized:
            self._set_badge("ANALYSIS ERROR", "failed")
        elif "complete" in normalized:
            self._set_badge("BRIEF READY", "complete")
        elif "retrieving" in normalized or "analyzing" in normalized:
            self._set_badge("ANALYZING", "running")
        elif not self.m_running:
            self._set_badge("SYSTEM READY", "ready")

    def set_result(self, result: CiaAnalysisResult) -> None:
        """Display the successful report and retain supporting articles."""
        self.m_last_result = result
        self._set_badge("BRIEF READY", "complete")
        report = result.report
        self.m_target.setText(f"TARGET: {report.ticker}")

        if report.has_breaking_news:
            status, catalyst_state = "BREAKING CATALYST DETECTED", "breaking"
        elif report.categories:
            status, catalyst_state = "ACTIVE CATALYST DETECTED", "active"
        else:
            status, catalyst_state = "NO ACTIVE CATALYST", "none"

        self.m_mission_status.setText(status)
        self.m_mission_status.setProperty("catalyst", catalyst_state)
        self.m_mission_status.style().unpolish(self.m_mission_status)
        self.m_mission_status.style().polish(self.m_mission_status)

        self.m_metrics["strength"].setText(report.catalyst_strength.value)
        self.m_metrics["freshness"].setText(report.freshness.value)
        self.m_metrics["sentiment"].setText(f"{report.overall_sentiment} ({report.average_sentiment:+.2f})")

        sentiment_value = self.m_metrics["sentiment"]
        sentiment_label = report.overall_sentiment.lower()

        if "bullish" in sentiment_label:
            signal = "positive"
        elif "bearish" in sentiment_label:
            signal = "negative"
        else:
            signal = "neutral"

        sentiment_value.setProperty("signal", signal)
        sentiment_value.style().unpolish(sentiment_value)
        sentiment_value.style().polish(sentiment_value)

        self.m_metrics["confidence"].setText(f"{report.confidence:.0%}")
        self.m_metrics["articles"].setText(f"{report.unique_article_count} / {report.original_article_count}")
        self.m_metrics["duplicates"].setText(str(report.duplicate_articles_removed))
        self.m_current.setText("\n".join(category.value for category in report.categories) or "None")
        self.m_historical.setText("\n".join(category.value for category in report.historical_categories) or "None")
        self.m_summary.setText(report.summary)
        self.m_sources.set_articles(result.articles)
        self.m_brief_scroll.show()
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

    def _set_badge(self, text: str, state: str) -> None:
        """Update the CIA header badge and refresh its scoped style."""
        self.m_system_badge.setText(text)
        self.m_system_badge.setProperty("state", state)
        self.m_system_badge.style().unpolish(self.m_system_badge)
        self.m_system_badge.style().polish(self.m_system_badge)
