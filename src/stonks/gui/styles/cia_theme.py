# =============================================================================
# File: cia_theme.py
# Purpose: Defines scoped visual styling for the CIA workspace foundation.
# =============================================================================

CIA_WORKSPACE_THEME = """
QWidget#ciaWorkspace {
    background-color: #101923;
    color: #edf3f8;
}

QLabel#ciaEyebrow, QLabel#ciaKicker {
    background: transparent;
    color: #65d9b5;
    font-size: 10px;
    font-weight: 700;
}

QLabel#ciaTitle {
    background: transparent;
    color: #f1f5f9;
    font-size: 24px;
    font-weight: 700;
}

QLabel#ciaSubtitle, QLabel#ciaHint {
    background: transparent;
    color: #94a3b8;
    font-size: 11px;
}

QFrame#ciaSearchPanel {
    background-color: #192532;
    border: 1px solid #2b3a48;
    border-radius: 10px;
}

QLabel#ciaSearchCaption {
    color: #f1f5f9;
    font-size: 14px;
    font-weight: 700;
    background: transparent;
}

QLineEdit#ciaTickerInput {
    background-color: #223241;
    color: #f1f5f9;
    border: 1px solid #3a5062;
    border-radius: 7px;
    padding: 9px 12px;
    selection-background-color: #285c59;
    selection-color: #ffffff;
    min-height: 20px;
}

QLineEdit#ciaTickerInput:hover:enabled {
    border-color: #617b8c;
}

QLineEdit#ciaTickerInput:focus {
    border-color: #65d9b5;
}

QLineEdit#ciaTickerInput:disabled {
    color: #738496;
    background-color: #1c2b36;
    border-color: #30414f;
}

QPushButton#ciaAnalyzeButton {
    background-color: #65d9b5;
    color: #102521;
    border: 1px solid #65d9b5;
    border-radius: 7px;
    padding: 9px 18px;
    font-weight: 700;
    text-align: center;
    min-height: 20px;
}

QPushButton#ciaAnalyzeButton:hover:enabled {
    background-color: #82e8c9;
}

QPushButton#ciaAnalyzeButton:pressed:enabled {
    background-color: #4dbf9d;
}

QPushButton#ciaAnalyzeButton:disabled {
    background-color: #354e4b;
    border-color: #354e4b;
    color: #8aa9a2;
}

QLabel#ciaStatus {
    background: transparent;
    color: #b9c9d5;
    font-size: 12px;
}

QLabel#ciaKicker {
    border: 1px solid #376b54;
    border-radius: 7px;
    padding: 6px 10px;
    background-color: #1c3b32;
}

QLabel#ciaKicker[state="running"] {
    color: #f4d58d;
    border-color: #75623d;
    background-color: #3a3225;
}

QLabel#ciaKicker[state="failed"] {
    color: #f28b91;
    border-color: #75464a;
    background-color: #39272d;
}

QLabel#ciaKicker[state="complete"] {
    color: #65d9b5;
}

QLabel#ciaKicker[state="ready"] {
    color: #65d9b5;
}
"""
