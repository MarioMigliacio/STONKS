# =============================================================================
# File: test_cia_article_dossier.py
# Purpose: Tests CIA dossier data display, navigation and source URL safety.
# =============================================================================

from datetime import datetime, timezone

from PySide6.QtWidgets import QApplication

from stonks.gui.widgets.cia_article_dossier import CiaArticleDossier
from stonks.models.news_article import NewsArticle


def _article(url: str = "https://example.com/story") -> NewsArticle:
    """Build an article with deterministic normalized fields."""
    return NewsArticle(
        title="AMD announces earnings",
        source="Test Wire",
        published_at=datetime(2026, 10, 28, 14, 30, tzinfo=timezone.utc),
        summary="AMD reported quarterly earnings.",
        url=url,
        sentiment_score=0.4,
        sentiment_label="Bullish",
    )


def test_dossier_displays_normalized_fields(qapp: QApplication) -> None:
    """Render the supplied evidence without network access."""
    dossier = CiaArticleDossier()
    article = _article()
    dossier.set_article(article)
    assert dossier.m_article is article
    assert dossier.m_headline.text() == article.title
    assert "Test Wire" in dossier.m_source.text()
    assert "2026-10-28 14:30" in dossier.m_source.text()
    assert "Earnings" in dossier.m_categories.text()
    assert "Bullish" in dossier.m_sentiment.text()
    assert article.summary == dossier.m_summary.text()
    assert dossier.m_open_button.isEnabled()


def test_invalid_publisher_url_disables_open(qapp: QApplication) -> None:
    """Never offer navigation to unsupported URL schemes."""
    dossier = CiaArticleDossier()
    dossier.set_article(_article("javascript:alert(1)"))
    assert not dossier.m_open_button.isEnabled()
    dossier.set_article(_article(""))
    assert not dossier.m_open_button.isEnabled()


def test_back_button_emits_navigation_signal(qapp: QApplication) -> None:
    """Expose back navigation without changing the article model."""
    dossier = CiaArticleDossier()
    requests = []
    dossier.back_requested.connect(lambda: requests.append(True))
    dossier.m_back_button.click()
    assert requests == [True]
