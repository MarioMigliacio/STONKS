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
"""
