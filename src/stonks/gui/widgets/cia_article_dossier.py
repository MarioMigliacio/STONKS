# =============================================================================
# File: cia_article_dossier.py
# Purpose: Displays normalized CIA article evidence in a navigable dossier.
# =============================================================================

from datetime import timezone
from typing import Optional

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_classifier import classify_article
from stonks.gui.icons import get_icon
from stonks.models.news_article import NewsArticle


class CiaArticleDossier(QWidget):
    """Display available article intelligence without fetching publisher content.

    Attributes:
        m_article:
            Currently displayed article, if any.

        m_back_button:
            Button requesting return to the Mission Brief.

        m_open_button:
            Button opening the original publisher URL.

        m_headline:
            Headline field.

        m_source:
            Publisher and publication timestamp field.

        m_categories:
            Classified catalyst categories field.

        m_sentiment:
            Provider sentiment field.

        m_summary:
            Provider-supplied summary field.

        m_url:
            Original source URL field.
    """

    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Build the scrollable dossier workspace."""
        super().__init__(parent)
        self.setObjectName("ciaDossier")
        self.m_article: Optional[NewsArticle] = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        navigation = QHBoxLayout()

        self.m_back_button = QPushButton("Back to Mission Brief")
        self.m_back_button.setObjectName("ciaDossierBack")
        self.m_back_button.setIcon(get_icon("arrow-left"))
        self.m_back_button.setIconSize(QSize(16, 16))
        self.m_back_button.clicked.connect(self.back_requested.emit)
        navigation.addWidget(self.m_back_button)
        navigation.addStretch()

        self.m_open_button = QPushButton("Open Original Article")
        self.m_open_button.setObjectName("ciaDossierOpen")
        self.m_open_button.clicked.connect(self._open_original)
        navigation.addWidget(self.m_open_button)
        layout.addLayout(navigation)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("ciaDossierScroll")
        body = QWidget()
        content = QVBoxLayout(body)
        content.setSpacing(16)
        eyebrow = QLabel("INTELLIGENCE DOSSIER / SOURCE RECORD")
        eyebrow.setObjectName("ciaEyebrow")
        content.addWidget(eyebrow)

        self.m_headline = self._field(content, "HEADLINE")
        self.m_source = self._field(content, "PUBLISHER / PUBLISHED (UTC)")
        self.m_categories = self._field(content, "CATALYST CLASSIFICATION")
        self.m_sentiment = self._field(content, "SENTIMENT")
        self.m_summary = self._field(content, "PROVIDER SUMMARY")
        self.m_url = self._field(content, "ORIGINAL SOURCE")
        note = QLabel(
            "This dossier shows normalized provider data, not the full "
            "publisher article. Open the original source for the full story."
        )
        note.setObjectName("ciaSectionBody")
        note.setWordWrap(True)
        content.addWidget(note)
        content.addStretch()
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        self.m_open_button.setEnabled(False)

    @staticmethod
    def _field(layout: QVBoxLayout, caption: str) -> QLabel:
        """Append a labeled selectable dossier field."""
        heading = QLabel(caption)
        heading.setObjectName("ciaSectionTitle")
        layout.addWidget(heading)
        value = QLabel("—")
        value.setObjectName("ciaSectionBody")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(value)
        return value

    def set_article(self, article: NewsArticle) -> None:
        """Populate the dossier from an existing normalized article."""
        self.m_article = article
        published = article.published_at

        if published.tzinfo is not None:
            published = published.astimezone(timezone.utc)

        categories = [category.value for category in classify_article(article) if category != CatalystCategory.UNKNOWN]
        self.m_headline.setText(article.title or "Untitled article")
        self.m_source.setText(f"{article.source or 'Unknown publisher'} / {published.strftime('%Y-%m-%d %H:%M')}")
        self.m_categories.setText(", ".join(categories) or "Unclassified")
        self.m_sentiment.setText(f"{article.sentiment_label or 'Unknown'} ({article.sentiment_score:+.2f})")
        self.m_summary.setText(article.summary or "No summary supplied by provider.")
        self.m_url.setText(article.url or "No source URL supplied.")
        self.m_open_button.setEnabled(self._valid_url(article.url))

    @staticmethod
    def _valid_url(url: str) -> bool:
        """Accept only absolute HTTP or HTTPS publisher URLs."""
        parsed = QUrl(url or "")
        return (
            parsed.isValid()
            and parsed.scheme().lower()
            in (
                "http",
                "https",
            )
            and bool(parsed.host())
        )

    def _open_original(self) -> None:
        """Open the publisher URL through the operating system."""
        if self.m_article is not None and self._valid_url(self.m_article.url):
            QDesktopServices.openUrl(QUrl(self.m_article.url))
