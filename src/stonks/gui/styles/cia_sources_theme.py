# =============================================================================
# File: cia_sources_theme.py
# Purpose: Provides scoped styles for the CIA Supporting Intelligence table.
# =============================================================================

CIA_SOURCES_THEME = """
QFrame#ciaSourcesPanel {
    background-color: #192532;
    border: 1px solid #2b3a48;
    border-radius: 10px;
}

QFrame#ciaSourcesPanel QLabel#ciaSourcesHeading {
    color: #f1f5f9;
    background: transparent;
    font-size: 14px;
    font-weight: 700;
}

QFrame#ciaSourcesPanel QLabel#ciaSourcesHint {
    color: #94a3b8;
    background: transparent;
    font-size: 11px;
}

QFrame#ciaSourcesPanel QLabel#ciaSourcesEmpty {
    color: #94a3b8;
    background-color: #223241;
    border: 1px dashed #3a5062;
    border-radius: 8px;
    padding: 18px;
    font-size: 12px;
}

QTableWidget#ciaSourcesTable {
    background-color: #192532;
    alternate-background-color: #20303e;
    color: #e8edf5;
    gridline-color: #2b3a48;
    border: 1px solid #344859;
    border-radius: 8px;
    selection-background-color: #285c59;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget#ciaSourcesTable::item {
    padding: 8px 10px;
    border-bottom: 1px solid #293c4b;
}

QTableWidget#ciaSourcesTable::item:hover:!selected {
    background-color: #294051;
}

QTableWidget#ciaSourcesTable::item:selected {
    background-color: #285c59;
    color: #ffffff;
}

QTableWidget#ciaSourcesTable QHeaderView::section {
    background-color: #223241;
    color: #a8b9c9;
    border: none;
    border-right: 1px solid #344859;
    border-bottom: 1px solid #344859;
    padding: 10px 12px;
    font-size: 10px;
    font-weight: 700;
}

QTableWidget#ciaSourcesTable QTableCornerButton::section {
    background-color: #223241;
    border: none;
}
"""
