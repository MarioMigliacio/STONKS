# =============================================================================
# File: cia_intelligence_sources.py
# Purpose: Displays classified supporting articles for a CIA Mission Brief.
# =============================================================================

from typing import Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_classifier import classify_article
from stonks.gui.icons import get_icon
from stonks.models.news_article import NewsArticle


class CiaIntelligenceSources(QFrame):
    """Display article-level evidence without fetching external content.

    Attributes:
        m_heading:
            Section heading showing the number of available sources.

        m_empty:
            Explanation shown when no articles are available.

        m_table:
            Keyboard-accessible table of normalized news articles.

        m_articles:
            Articles in the same order as the displayed rows.
    """

    article_activated = Signal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the supporting-intelligence section."""
        super().__init__(parent)
        self.setObjectName("ciaSourcesPanel")
        self.m_articles: list[NewsArticle] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        heading_row = QHBoxLayout()
        heading_row.setSpacing(9)
        heading_icon = QLabel()
        heading_icon.setPixmap(get_icon("newspaper").pixmap(QSize(18, 18)))
        heading_icon.setFixedSize(18, 18)
        heading_row.addWidget(heading_icon)

        self.m_heading = QLabel("Supporting Intelligence / 0")
        self.m_heading.setObjectName("ciaSourcesHeading")
        heading_row.addWidget(self.m_heading)
        heading_row.addStretch()
        layout.addLayout(heading_row)

        hint = QLabel("Double-click an article or press Enter to open its dossier.")
        hint.setObjectName("ciaSourcesHint")
        layout.addWidget(hint)

        self.m_empty = QLabel("No supporting articles available for this briefing.")
        self.m_empty.setObjectName("ciaSourcesEmpty")
        self.m_empty.setWordWrap(True)
        layout.addWidget(self.m_empty)

        self.m_table = QTableWidget(0, 4)
        self.m_table.setObjectName("ciaSourcesTable")
        self.m_table.setHorizontalHeaderLabels(["CATALYST", "HEADLINE / SOURCE", "PUBLISHED (UTC)", "SENTIMENT"])
        self.m_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.m_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.m_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.m_table.setAlternatingRowColors(True)
        self.m_table.setWordWrap(True)
        self.m_table.setShowGrid(False)
        self.m_table.setFocusPolicy(Qt.StrongFocus)
        self.m_table.setSortingEnabled(False)
        self.m_table.horizontalHeader().setHighlightSections(False)
        self.m_table.verticalHeader().setDefaultSectionSize(62)
        self.m_table.verticalHeader().hide()
        self.m_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.m_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.m_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.m_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.m_table.cellDoubleClicked.connect(self._activate_row)
        self.m_table.itemActivated.connect(self._activate_item)
        self.m_table.setMinimumHeight(170)
        layout.addWidget(self.m_table)
        self.m_table.hide()

    def set_articles(self, articles: list[NewsArticle]) -> None:
        """Replace rows with the available deduplicated article evidence."""
        self.m_articles = list(articles)
        self.m_heading.setText(f"Supporting Intelligence - {len(self.m_articles)}")
        self.m_table.setRowCount(len(self.m_articles))

        for row, article in enumerate(self.m_articles):
            categories = [category for category in classify_article(article) if category != CatalystCategory.UNKNOWN]
            catalyst = ", ".join(category.value for category in categories)

            if not catalyst:
                catalyst = "Unclassified"
            published = article.published_at

            if published.tzinfo is not None:
                from datetime import timezone

                published = published.astimezone(timezone.utc)
            timestamp = published.strftime("%Y-%m-%d %H:%M")
            cells = (
                catalyst,
                f"{article.title or 'Untitled article'}\n{article.source or 'Unknown source'}",
                timestamp,
                article.sentiment_label or "Unknown",
            )

            for column, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.m_table.setItem(row, column, item)

            self.m_table.resizeRowToContents(row)

        visible_rows = min(len(self.m_articles), 3)

        rows_height = sum(self.m_table.rowHeight(row) for row in range(visible_rows))

        header_height = self.m_table.horizontalHeader().height()
        frame_height = self.m_table.frameWidth() * 2

        self.m_table.setMinimumHeight(max(170, rows_height + header_height + frame_height + 8))

        self.m_table.clearSelection()
        self.m_empty.setVisible(not self.m_articles)
        self.m_table.setVisible(bool(self.m_articles))

    def _activate_row(self, row: int, column: int) -> None:
        """Signal the selected article for the future dossier workspace."""
        if 0 <= row < len(self.m_articles):
            self.article_activated.emit(self.m_articles[row])

    def _activate_item(self, item: QTableWidgetItem) -> None:
        """Support Enter-key activation of the selected article."""
        self._activate_row(item.row(), item.column())
