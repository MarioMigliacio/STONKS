# =============================================================================
# File: test_research_integration.py
# Purpose: Verifies Research navigation and workspace integration in MainWindow.
# =============================================================================

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QPushButton

from stonks.gui.main_window import MainWindow
from stonks.gui.pages.research_page import ResearchPage
from stonks.models.historical_research_request import HistoricalResearchRequest


def test_research_page_is_registered_and_sidebar_navigates(qtbot):
    """The sidebar opens the real ResearchPage, not a placeholder."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.m_pages.count() == 6
    assert isinstance(window.m_research_page, ResearchPage)
    assert window.m_pages.widget(window.m_page_indices["research"]) is window.m_research_page

    research_button = next(
        button for button in window.m_sidebar.findChildren(QPushButton) if button.text() == "Historical Research"
    )
    qtbot.mouseClick(research_button, Qt.LeftButton)

    assert window.m_pages.currentWidget() is window.m_research_page
    assert research_button.isChecked()


def test_research_request_is_emitted_from_registered_page(qtbot):
    """MainWindow exposes a working request signal for future execution wiring."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    page = window.m_research_page
    assert page is not None
    window._navigate_to("research")
    page.m_ticker_input.setText("AMD")
    spy = QSignalSpy(page.research_requested)

    qtbot.mouseClick(page.m_analyze_button, Qt.LeftButton)

    assert spy.count() == 1
    assert isinstance(spy.at(0)[0], HistoricalResearchRequest)
    assert page.m_presentation_state == "loading"
    assert not page.m_analyze_button.isEnabled()


def test_research_theme_and_icons_are_loaded(qtbot):
    """Research workspace follows scoped styling and uses existing SVG assets."""
    page = ResearchPage()
    qtbot.addWidget(page)

    assert "QWidget#researchWorkspace" in page.styleSheet()
    assert not page.m_analyze_button.icon().isNull()
    assert not page.m_refresh_button.icon().isNull()
    assert page.m_status_label.property("state") == "ready"
    page.show_loading()
    assert page.m_status_label.property("state") == "running"
    page.show_error("Test failure")
    assert page.m_status_label.property("state") == "failed"
