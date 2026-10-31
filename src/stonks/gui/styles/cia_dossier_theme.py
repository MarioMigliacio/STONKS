# =============================================================================
# File: cia_dossier_theme.py
# Purpose: Styles the CIA Article Dossier with scoped dark-terminal components.
# =============================================================================

CIA_DOSSIER_THEME = """
QWidget#ciaDossier, QWidget#ciaDossierBody {
    background: #101923;
}

QPushButton#ciaDossierBack {
    background: #223241; color: #c4d0df; border: 1px solid #344859;
    border-radius: 7px; padding: 9px 14px; font-weight: 700;
}

QPushButton#ciaDossierBack:hover { background: #2c4052; color: #f1f5f9; }
QPushButton#ciaDossierOpen {
    background: #65d9b5;
    color: #102521;
    border: 1px solid #65d9b5;
    border-radius: 7px;
    padding: 9px 14px;
    font-weight: 700;
}

QPushButton#ciaDossierOpen:hover:enabled { background: #82e8c9; }
QPushButton#ciaDossierOpen:disabled {
    background: #354e4b;
    border-color: #354e4b;
    color: #8aa9a2;
}

QLabel#ciaDossierEyebrow {
    background: transparent;
    color: #65d9b5;
    font-size: 10px;
    font-weight: 700;
}

QLabel#ciaDossierHeadline {
    background: transparent;
    color: #f1f5f9;
    font-size: 19px;
    font-weight: 700;
}

QFrame#ciaDossierCard {
    background: #192532;
    border: 1px solid #2b3a48;
    border-radius: 10px;
}

QLabel#ciaDossierCaption {
    background: transparent;
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
}

QLabel#ciaDossierValue {
    background: transparent;
    color: #edf3f8;
    font-size: 12px;
}

QLabel#ciaDossierValue[signal="positive"] { color: #65d9b5; }
QLabel#ciaDossierValue[signal="negative"] { color: #f28b91; }
QLabel#ciaDossierNote {
    background: transparent;
    color: #94a3b8;
    font-size: 11px;
}
"""
