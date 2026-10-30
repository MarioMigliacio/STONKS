# =============================================================================
# File: test_cia_dossier_url_integration.py
# Purpose: Verifies the dossier opens the normalized publisher URL safely.
# =============================================================================

from datetime import datetime, timezone
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from stonks.gui.widgets.cia_article_dossier import CiaArticleDossier
from stonks.models.news_article import NewsArticle


def test_open_original_invokes_desktop_service(qapp: QApplication) -> None:
    """Open the publisher URL through Qt without launching a browser in tests."""
    article = NewsArticle(
        title="AMD earnings",
        source="Test Wire",
        published_at=datetime(2026, 10, 28, tzinfo=timezone.utc),
        summary="Earnings released.",
        url="https://example.com/story",
        sentiment_score=0.4,
        sentiment_label="Bullish",
    )
    dossier = CiaArticleDossier()
    dossier.set_article(article)

    with patch(
        "stonks.gui.widgets.cia_article_dossier.QDesktopServices.openUrl",
        return_value=True,
    ) as open_url:
        dossier.m_open_button.click()

    open_url.assert_called_once()
    assert open_url.call_args.args[0].toString() == article.url
