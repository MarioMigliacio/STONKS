# =============================================================================
# File: theme.py
# Purpose: Defines the centralized visual theme for the STONKS GUI.
# =============================================================================

STONKS_DARK_THEME = """
QMainWindow {
    background-color: #141A23;
}

QWidget {
    background-color: #141A23;
    color: #E8EDF5;
    font-family: "Segoe UI";
    font-size: 13px;
}

QFrame#navigationSidebar {
    background-color: #1C2532;
    border-right: 1px solid #344154;
}

QFrame#navigationSidebar QLabel {
    background-color: transparent;
}

QLabel#applicationTitle {
    color: #59A8FF;
    font-size: 24px;
    font-weight: bold;
    padding: 12px;
}

QPushButton {
    background-color: #263346;
    color: #CED7E4;
    border: none;
    border-radius: 6px;
    padding: 12px 16px;
    text-align: left;
}

QPushButton:hover {
    background-color: #354761;
    color: #FFFFFF;
}

QPushButton:checked {
    background-color: #235C93;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton:focus {
    outline: none;
}

QTableWidget {
    background-color: #141A23;
    alternate-background-color: #1C2532;
    color: #E8EDF5;
    gridline-color: #344154;
    border: 1px solid #344154;
    border-radius: 6px;
    selection-background-color: #235C93;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #263346;
    color: #E8EDF5;
    border: none;
    border-right: 1px solid #344154;
    border-bottom: 1px solid #344154;
    padding: 8px 12px;
    font-weight: bold;
}

QTableCornerButton::section {
    background-color: #263346;
    border: none;
}

QTableWidget QTableWidgetItem {
    color: #E8EDF5;
}

QMenu {
    background-color: #171D28;
    color: #E8EDF5;
    border: 1px solid #344055;
    padding: 5px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #263C59;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background-color: #45566F;
    margin: 6px 10px;
}
"""
