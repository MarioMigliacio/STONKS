# =============================================================================
# File: test_cia_intelligence_sources.py
# Purpose: Verifies CIA supporting-article display and selection behavior.
# =============================================================================

from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

from stonks.gui.widgets.cia_intelligence_sources import CiaIntelligenceSources
from stonks.models.news_article import NewsArticle


def _article(title: str) -> NewsArticle:
    """Create a normalized test article."""
    return NewsArticle(
        title=title,
        source="Test Wire",
        published_at=datetime(2026, 10, 28, 14, 30, tzinfo=timezone.utc),
        summary="Company announced an earnings report.",
        url="https://example.com/article",
        sentiment_score=0.4,
        sentiment_label="Bullish",
    )


def test_empty_sources(qapp: QApplication) -> None:
    """Empty evidence does not render a misleading article row."""
    widget = CiaIntelligenceSources()
    widget.set_articles([])
    assert widget.m_table.rowCount() == 0
    assert widget.m_empty.isVisibleTo(widget)


def test_sources_show_classification_and_metadata(qapp: QApplication) -> None:
    """Each article exposes its headline, source, timestamp and catalyst."""
    widget = CiaIntelligenceSources()
    widget.set_articles([_article("Earnings released")])
    assert widget.m_table.rowCount() == 1
    assert "Earnings" in widget.m_table.item(0, 0).text()
    assert "Test Wire" in widget.m_table.item(0, 1).text()
    assert "2026-10-28" in widget.m_table.item(0, 2).text()
    assert widget.m_table.item(0, 3).text() == "Bullish"


def test_double_click_activates_original_article(qapp: QApplication) -> None:
    """Activation forwards the original normalized model, not row text."""
    article = _article("Earnings released")
    widget = CiaIntelligenceSources()
    widget.set_articles([article])
    activated = []
    widget.article_activated.connect(activated.append)
    widget._activate_row(0, 1)
    assert activated == [article]
