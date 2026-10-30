# =============================================================================
# File: test_cia_workspace_integration.py
# Purpose: Verifies CIA briefing navigation and main-window worker integration.
# =============================================================================

from datetime import datetime, timezone
from threading import Event
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from stonks.cia.cia_analysis_result import CiaAnalysisResult
from stonks.gui.main_window import MainWindow
from stonks.gui.pages.cia_page import CiaPage
from stonks.models.news_article import NewsArticle


def _result(ticker: str = "AMD") -> CiaAnalysisResult:
    """Create deterministic intelligence with two supporting articles."""
    articles = [
        NewsArticle(
            title=f"{ticker} announces earnings {index}",
            source="Test Wire",
            published_at=datetime(2026, 10, 28, 14, 30, tzinfo=timezone.utc),
            summary=f"{ticker} reported earnings.",
            url=f"https://example.com/{ticker.lower()}/{index}",
            sentiment_score=0.4,
            sentiment_label="Bullish",
        )
        for index in range(2)
    ]
    report = Mock()
    report.ticker = ticker
    report.has_breaking_news = False
    report.categories = []
    report.historical_categories = []
    report.catalyst_strength.value = "Moderate"
    report.freshness.value = "Recent"
    report.overall_sentiment = "Bullish"
    report.average_sentiment = 0.4
    report.confidence = 0.75
    report.unique_article_count = 2
    report.original_article_count = 2
    report.duplicate_articles_removed = 0
    report.summary = f"{ticker} reported earnings."
    return CiaAnalysisResult(report=report, articles=articles)


def test_dossier_round_trip_preserves_briefing_and_selection(qtbot) -> None:
    """Returning from a dossier retains the report, row, and scroll position."""
    page = CiaPage()
    qtbot.addWidget(page)
    page.show()
    result = _result()
    page.set_result(result)
    table = page.m_sources.m_table
    table.selectRow(1)
    page.m_brief_scroll.verticalScrollBar().setValue(page.m_brief_scroll.verticalScrollBar().maximum())
    position = page.m_brief_scroll.verticalScrollBar().value()

    page.m_sources._activate_row(1, 1)
    assert page.m_view_stack.currentWidget() is page.m_dossier
    assert page.m_dossier.m_article is result.articles[1]
    page.m_dossier.m_back_button.click()

    assert page.m_view_stack.currentWidget() is page.m_brief_scroll
    assert page.m_last_result is result
    assert table.currentRow() == 1
    assert table.selectedItems()
    assert page.m_brief_scroll.verticalScrollBar().value() == position


def test_new_success_replaces_dossier_and_returns_to_briefing(qtbot) -> None:
    """A new successful analysis replaces the old briefing and dossier view."""
    page = CiaPage()
    qtbot.addWidget(page)
    page.set_result(_result("AMD"))
    page.m_sources._activate_row(0, 1)
    assert page.m_view_stack.currentWidget() is page.m_dossier

    replacement = _result("NVDA")
    page.set_result(replacement)

    assert page.m_last_result is replacement
    assert page.m_target.text() == "TARGET: NVDA"
    assert page.m_view_stack.currentWidget() is page.m_brief_scroll
    assert page.m_sources.m_articles == replacement.articles
    assert page.m_sources.m_table.rowCount() == 2


def test_main_window_failure_preserves_result_and_recovers_controls(qtbot) -> None:
    """Worker failure reaches MainWindow and retains previously shown evidence."""
    window = MainWindow()
    qtbot.addWidget(window)
    page = window.m_cia_page
    result = _result()
    page.set_result(result)
    service = Mock()
    service.analyze.side_effect = RuntimeError("Provider unavailable")
    window.m_cia_controller.m_service_factory = lambda: service

    assert window.m_cia_controller.start_analysis("AMD")
    qtbot.waitUntil(lambda: not window.m_cia_controller.is_running(), timeout=5000)
    QApplication.processEvents()

    assert page.m_last_result is result
    assert page.m_target.text() == "TARGET: AMD"
    assert page.m_sources.m_articles == result.articles
    assert "Provider unavailable" in page.m_status_label.text()
    assert page.m_analyze_button.isEnabled()
    assert page.m_ticker_input.isEnabled()


def test_close_waits_for_active_cia_worker(qtbot) -> None:
    """Close is deferred until an active blocking CIA request finishes."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    entered = Event()
    release = Event()
    service = Mock()

    def analyze(ticker: str, limit: int = 50) -> CiaAnalysisResult:
        entered.set()
        if not release.wait(4):
            raise TimeoutError("Controlled test request timed out")
        return _result(ticker)

    service.analyze.side_effect = analyze
    window.m_cia_controller.m_service_factory = lambda: service

    try:
        assert window.m_cia_controller.start_analysis("AMD")
        qtbot.waitUntil(entered.is_set, timeout=2000)
        assert window.close() is False
        assert window.isVisible()
        assert window.m_close_pending
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.m_cia_controller.is_running(), timeout=5000)
        qtbot.waitUntil(lambda: not window.isVisible(), timeout=2000)

    assert not window.m_close_pending
