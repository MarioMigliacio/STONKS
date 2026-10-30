# =============================================================================
# File: test_cia_page.py
# Purpose: Tests CIA Mission Brief state preservation and request controls.
# =============================================================================

from datetime import datetime, timezone
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from stonks.cia.cia_analysis_result import CiaAnalysisResult
from stonks.gui.pages.cia_page import CiaPage
from stonks.models.news_article import NewsArticle


def _result() -> CiaAnalysisResult:
    """Create a successful CIA result for GUI state testing."""
    article = NewsArticle(
        title="AMD announces earnings",
        source="Test Wire",
        published_at=datetime(2026, 10, 28, 14, 30, tzinfo=timezone.utc),
        summary="AMD reported quarterly earnings.",
        url="https://example.com/article",
        sentiment_score=0.4,
        sentiment_label="Bullish",
    )

    report = Mock()
    report.ticker = "AMD"
    report.has_breaking_news = False
    report.categories = []
    report.historical_categories = []
    report.catalyst_strength.value = "Moderate"
    report.freshness.value = "Recent"
    report.overall_sentiment = "Bullish"
    report.average_sentiment = 0.4
    report.confidence = 0.75
    report.unique_article_count = 1
    report.original_article_count = 1
    report.duplicate_articles_removed = 0
    report.summary = "AMD reported quarterly earnings."

    return CiaAnalysisResult(
        report=report,
        articles=[article],
    )


def test_failed_analysis_preserves_previous_briefing(
    qapp: QApplication,
) -> None:
    """Retain successful intelligence when a later analysis fails."""
    page = CiaPage()
    result = _result()

    page.set_result(result)

    original_target = page.m_target.text()
    original_summary = page.m_summary.text()
    original_article_count = page.m_sources.m_table.rowCount()

    # Simulate a second analysis that encounters a provider failure.
    page.set_running(True)
    page.set_status("CIA analysis failed: Marketaux request failed for AMD.")
    page.set_running(False)

    assert page.m_last_result is result
    assert page.m_target.text() == original_target
    assert page.m_summary.text() == original_summary
    assert page.m_sources.m_table.rowCount() == original_article_count

    assert page.m_analyze_button.isEnabled()
    assert page.m_ticker_input.isEnabled()
    assert "Marketaux request failed" in page.m_status_label.text()
